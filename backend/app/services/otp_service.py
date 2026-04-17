from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets


@dataclass
class OTPRecord:
    email: str
    code: str
    expires_at: datetime


def create_otp(email: str, expiry_minutes: int = 5) -> OTPRecord:
    code = f"{secrets.randbelow(1000000):06d}"
    return OTPRecord(
        email=email,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )

def is_valid_otp(record: OTPRecord, code: str) -> bool:
    return datetime.utcnow() <= record.expires_at and record.code == code