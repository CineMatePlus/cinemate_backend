from pydantic import BaseModel
from typing import Optional
from app.models.user import UserResponse, Gender


class Token(BaseModel):
    """JWT token modeli"""

    access_token: str


class TokenData(BaseModel):
    """Token veri modeli"""

    username: Optional[str] = None


class RegisterRequest(BaseModel):
    """Kayıt isteği modeli"""

    email: str
    name: str
    password: str
    gender: Gender = Gender.OTHER


class LoginRequest(BaseModel):
    """Giriş isteği modeli"""

    email: str
    password: str


class AuthResponse(BaseModel):
    """Kimlik doğrulama yanıt modeli"""
    user: UserResponse
    access_token: str
