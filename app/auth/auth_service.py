import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from app.database import get_database
from app.auth.otp_service import normalize_phone

async def get_or_create_user(phone: str) -> Dict[str, Any]:
    """
    Finds existing user by phone or automatically creates a new user model
    containing id, phone, createdAt, and lastLogin.
    """
    db = get_database()
    clean_phone = normalize_phone(phone)
    now = datetime.utcnow()

    user = await db.users.find_one({"phone": clean_phone})
    if not user:
        user_doc = {
            "phone": clean_phone,
            "createdAt": now,
            "lastLogin": now
        }
        result = await db.users.insert_one(user_doc)
        user = await db.users.find_one({"_id": result.inserted_id})

    else:
        # Update last login timestamp
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"lastLogin": now}}
        )
        user["lastLogin"] = now

    user["_id"] = str(user["_id"])
    return user

async def create_dev_session(user_id: str) -> str:
    """
    Creates a temporary development session token for the user.
    Session authentication is modular so JWT can replace it in production.
    """
    db = get_database()
    token = uuid.uuid4().hex
    session_doc = {
        "token": token,
        "user_id": user_id,
        "createdAt": datetime.utcnow()
    }
    await db.sessions.insert_one(session_doc)
    return token

async def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieves the authenticated user corresponding to a session token."""
    db = get_database()
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None

    if not ObjectId.is_valid(session["user_id"]):
        return None

    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def delete_session(token: str) -> bool:
    """Clears the development session state upon logout."""
    db = get_database()
    result = await db.sessions.delete_one({"token": token})
    return result.deleted_count > 0
