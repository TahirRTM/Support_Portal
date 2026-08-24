from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class OTPRequest(BaseModel):
    case_number: str = Field(max_length=32)
    email: EmailStr


class OTPVerify(BaseModel):
    case_number: str = Field(max_length=32)
    email: EmailStr
    code: str = Field(min_length=4, max_length=10)


class ClientSessionToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
