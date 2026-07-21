import hashlib
import random
from datetime import datetime, timedelta
from typing import Tuple, Optional
from app.database import get_database

OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 5

def normalize_phone(phone: str) -> str:
    """
    Strips all non-digit characters.
    If phone is 10 digits, prepends Indian country code '91'.
    """
    clean = "".join(filter(str.isdigit, phone))
    if len(clean) == 10:
        clean = "91" + clean
    return clean

def hash_otp(otp: str) -> str:
    """Computes SHA-256 hash of the OTP string."""
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()

async def create_and_store_otp(phone: str) -> Tuple[str, dict]:
    """
    Invalidates any previous OTP for the phone, generates a new 6-digit OTP,
    hashes it, and stores the record in MongoDB.
    Returns (raw_otp, stored_doc).
    """
    db = get_database()
    clean_phone = normalize_phone(phone)

    # Invalidate previous OTP records for this phone number
    await db.otps.delete_many({"phone": clean_phone})

    # Generate 6-digit OTP
    raw_otp = str(random.randint(100000, 999999))
    otp_hash = hash_otp(raw_otp)

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_doc = {
        "phone": clean_phone,
        "otpHash": otp_hash,
        "createdAt": now,
        "expiresAt": expires_at,
        "attempts": 0,
        "verified": False
    }

    result = await db.otps.insert_one(otp_doc)
    otp_doc["_id"] = str(result.inserted_id)
    return raw_otp, otp_doc

async def verify_otp_code(phone: str, input_otp: str) -> Tuple[bool, str]:
    """
    Validates input_otp against the latest active OTP record in MongoDB.
    Enforces expiry, max attempts limit, and SHA-256 hash match.
    """
    db = get_database()
    clean_phone = normalize_phone(phone)

    # Find the latest OTP record for this phone number
    otp_doc = await db.otps.find_one({"phone": clean_phone}, sort=[("createdAt", -1)])
    if not otp_doc:
        return False, "No active OTP found for this phone number. Please request a new OTP."

    if otp_doc.get("verified", False):
        return False, "OTP has already been used. Please request a new OTP."

    attempts = otp_doc.get("attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        return False, f"Maximum attempts limit ({MAX_ATTEMPTS}) exceeded. Please request a new OTP."

    now = datetime.utcnow()
    if now > otp_doc["expiresAt"]:
        return False, "OTP has expired. Please request a new OTP."

    # Compare SHA-256 hash
    input_hash = hash_otp(input_otp.strip())
    if input_hash == otp_doc["otpHash"]:
        # Mark as verified and remove to prevent reuse
        await db.otps.delete_one({"_id": otp_doc["_id"]})
        return True, "OTP verified successfully."
    else:
        # Increment attempt count
        new_attempts = attempts + 1
        await db.otps.update_one(
            {"_id": otp_doc["_id"]},
            {"$set": {"attempts": new_attempts}}
        )
        remaining = MAX_ATTEMPTS - new_attempts
        if remaining <= 0:
            return False, "Invalid OTP code. Maximum attempts limit reached."
        return False, f"Invalid OTP code. {remaining} attempts remaining."
