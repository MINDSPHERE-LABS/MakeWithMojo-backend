from fastapi import APIRouter, HTTPException, status, Header, Depends, Request
from typing import Optional
from app.auth.models import SendOTPRequest, VerifyOTPRequest
from app.auth.otp_service import create_and_store_otp, verify_otp_code, normalize_phone
from app.auth.auth_service import get_or_create_user, create_dev_session, get_user_by_session, delete_session
from app.services.whatsapp_service import whatsapp_service
from app.auth.rate_limiter import rate_limiter, get_client_ip

router = APIRouter(tags=["Authentication"])

def extract_token(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)) -> Optional[str]:
    """Helper to extract dev session token from Authorization or x-auth-token header."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split("Bearer ")[1].strip()
    if x_auth_token:
        return x_auth_token.strip()
    return None

@router.post("/send-otp")
@router.post("/auth/send-otp")
@router.post("/api/auth/send-otp")
async def send_otp(payload: SendOTPRequest, request: Request):
    """
    1. Validates phone number.
    2. Enforces 3 requests/minute rate limit.
    3. Generates 6-digit OTP and dispatches via Meta WhatsApp API.
    """
    if not payload.phone or len(payload.phone.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid mobile phone number."
        )

    clean_phone = normalize_phone(payload.phone)
    client_ip = get_client_ip(request)

    # Rate limiting: Max 3 OTP requests per 2 minutes (120s)
    rate_limiter.check_rate_limit(
        identifier=f"send_otp:{client_ip}:{clean_phone}",
        max_requests=3,
        window_seconds=120,
        custom_message="Too many OTP requests for this number. Please wait 2 minutes (120 seconds) before requesting another OTP."
    )

    raw_otp, otp_doc = await create_and_store_otp(clean_phone)

    # Deliver OTP via Meta WhatsApp API
    wa_res = await whatsapp_service.send_otp_message(clean_phone, raw_otp)

    return {
        "success": True,
        "message": "OTP verification code dispatched via WhatsApp.",
        "phone": clean_phone,
        "whatsapp_delivery": wa_res
    }

@router.post("/verify-otp")
@router.post("/auth/verify-otp")
@router.post("/api/auth/verify-otp")
async def verify_otp(payload: VerifyOTPRequest, request: Request):
    """
    1. Enforces 5 attempts per 2 minutes rate limit.
    2. Verifies 6-digit OTP against stored hash (2 min expiry).
    3. Auto-creates user if non-existent & returns session token.
    """
    if not payload.phone or not payload.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number and 6-digit OTP are required."
        )

    clean_phone = normalize_phone(payload.phone)
    client_ip = get_client_ip(request)

    # Rate limiting: Max 5 attempts per 2 minutes (120s)
    rate_limiter.check_rate_limit(
        identifier=f"verify_otp:{client_ip}:{clean_phone}",
        max_requests=5,
        window_seconds=120,
        custom_message="Too many OTP verification attempts. Please wait 2 minutes (120 seconds) before trying again."
    )

    valid, msg = await verify_otp_code(clean_phone, payload.otp)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # Auto-create or fetch user
    user = await get_or_create_user(clean_phone)
    
    # Establish dev session
    token = await create_dev_session(user["_id"])

    return {
        "success": True,
        "message": "OTP verified successfully.",
        "token": token,
        "user": {
            "id": user["_id"],
            "phone": user["phone"],
            "name": user.get("name"),
            "email": user.get("email")
        }
    }

@router.get("/me")
@router.get("/auth/me")
@router.get("/api/auth/me")
async def get_me(token: Optional[str] = Depends(extract_token)):
    """
    Exposes development authentication status.
    Returns authenticated state and current user info.
    """
    if not token:
        return {"authenticated": False, "user": None}

    user = await get_user_by_session(token)
    if not user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "id": user["_id"],
            "phone": user["phone"],
            "name": user.get("name"),
            "email": user.get("email")
        }
    }

@router.post("/logout")
@router.post("/auth/logout")
@router.post("/api/auth/logout")
async def logout(token: Optional[str] = Depends(extract_token)):
    """Clears development authentication state."""
    if token:
        await delete_session(token)
    return {
        "success": True,
        "message": "Logged out successfully."
    }
