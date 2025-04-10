from fastapi import Depends, HTTPException, Request
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

from app.database.mongo import user_collection
import os
from dotenv import load_dotenv


# Şifre hashleme için passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


# Şifreyi hash'leme
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Şifreyi doğrulama
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Access token oluşturma
def create_access_token(
    data: dict, expires_delta: timedelta = timedelta(minutes=30)
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Refresh token oluşturma (aynı işlemi yapıyor, sadece süre farklı)
def create_refresh_token(
    data: dict, expires_delta: timedelta = timedelta(days=7)
) -> str:
    return create_access_token(data, expires_delta)


# Middleware tarafından ayarlanan kullanıcıyı almak
async def get_current_user(request: Request):
    user = request.state.user  # Middleware'de ayarladığımız kullanıcıyı alıyoruz
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"email": user["email"], "id": str(user["_id"])}


# Token'ı çözme işlemi, genellikle middleware'de yapılır, ancak burada da kullanılabilir
def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
