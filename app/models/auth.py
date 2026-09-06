from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings
from app.models.user import Gender, UserResponse


def validate_password_policy(password: str) -> str:
    """Apply the configured policy and bcrypt's UTF-8 input limit."""
    if not password.strip():
        raise ValueError("Password cannot be blank or whitespace-only")
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        )
    if len(password) > settings.PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must be at most {settings.PASSWORD_MAX_LENGTH} characters"
        )
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return password


class Token(BaseModel):
    """JWT token modeli"""

    access_token: str


class TokenData(BaseModel):
    """Token veri modeli"""

    username: Optional[str] = None
    token_type: Optional[Literal["access", "refresh"]] = None
    jti: Optional[str] = None
    family_id: Optional[str] = None


class RegisterRequest(BaseModel):
    """Kayıt isteği modeli"""

    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str
    gender: Gender = Gender.OTHER

    _validate_password = field_validator("password")(validate_password_policy)


class LoginRequest(BaseModel):
    """Giriş isteği modeli"""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str

    _validate_new_password = field_validator("new_password")(validate_password_policy)


class AuthResponse(BaseModel):
    """Kimlik doğrulama yanıt modeli"""

    user: UserResponse
    token_type: Literal["bearer"] = "bearer"
    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int
