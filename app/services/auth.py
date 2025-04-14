from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Header
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import UserInDB, UserResponse
from app.models.auth import TokenData, AuthResponse
from app.db.mongodb import get_database

# Şifreleme ayarları
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self):
        self.db = get_database()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifre doğrulama"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Şifre hashleme"""
        return pwd_context.hash(password)

    async def get_user(self, username: str) -> Optional[UserInDB]:
        """Kullanıcı getirme"""
        user = await self.db.users.find_one({"email": username})
        if user:
            # MongoDB'den gelen veriyi düzenle
            user_data = {
                "_id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "hashed_password": user["hashed_password"],
                "is_active": user.get("is_active", True),
                "created_at": user.get("created_at", datetime.utcnow()),
                "updated_at": user.get("updated_at", datetime.utcnow()),
            }
            return UserInDB(**user_data)
        return None

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserInDB]:
        """Kullanıcı kimlik doğrulama"""
        user = await self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """JWT token oluşturma"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def get_current_user(self, token: str) -> UserInDB:
        """Mevcut kullanıcıyı getirme"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        user = await self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def get_user_from_token(self, authorization: str) -> AuthResponse:
        """Authorization header'ından kullanıcı bilgilerini getir"""
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        token = authorization.replace("Bearer ", "")
        try:
            user = await self.get_current_user(token)
            return UserResponse(
                    _id=user.id,
                    email=user.email,
                    name=user.name,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def register_user(self, user_data: dict) -> AuthResponse:
        """Yeni kullanıcı kaydı ve token oluşturma"""
        # Kullanıcının var olup olmadığını kontrol et
        existing_user = await self.get_user(user_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Kullanıcıyı oluştur
        hashed_password = self.get_password_hash(user_data["password"])
        user_dict = {
            "email": user_data["email"],
            "name": user_data["name"],
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Kullanıcıyı veritabanına ekle
        result = await self.db.users.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        # Token oluştur
        access_token = self.create_access_token(
            data={"sub": user_data["email"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return AuthResponse(
            user=UserResponse(
                _id=user_dict["_id"],
                email=user_dict["email"],
                name=user_dict["name"],
                created_at=user_dict["created_at"],
                updated_at=user_dict["updated_at"]
            ),
            access_token=access_token
        )

    async def login_user(self, username: str, password: str) -> AuthResponse:
        """Kullanıcı girişi ve token oluşturma"""
        user = await self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Token oluştur
        access_token = self.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return AuthResponse(
            user=UserResponse(
                _id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            ),
            access_token=access_token
        )

    async def refresh_token(self, authorization: str) -> AuthResponse:
        """Mevcut token'ı yeniler"""
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        token = authorization.replace("Bearer ", "")
        try:
            user = await self.get_current_user(token)
            
            # Yeni token oluştur
            new_token = self.create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            return AuthResponse(
                user=UserResponse(
                    _id=user.id,
                    email=user.email,
                    name=user.name,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                ),
                access_token=new_token
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
