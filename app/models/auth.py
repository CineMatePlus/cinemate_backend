from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT token modeli"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token veri modeli"""

    username: Optional[str] = None


class RegisterRequest(BaseModel):
    """Kayıt isteği modeli"""

    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    """Giriş isteği modeli"""

    email: str
    password: str
