from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class OTPRecord(BaseModel):
    phone: str
    otp_hash: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    verified: bool = False

class AuthUser(BaseModel):
    id: str
    phone: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
