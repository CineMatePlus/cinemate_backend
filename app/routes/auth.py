from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserInDB, UserResponse
from app.models.auth import Token, RegisterRequest
from app.services.auth import AuthService
from app.core.config import settings
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

# Servis örneği
auth_service = AuthService()


@router.post("/register", response_model=Token)
async def register(user_data: RegisterRequest):
    """Yeni kullanıcı kaydı"""
    # Kullanıcının var olup olmadığını kontrol et
    existing_user = await auth_service.get_user(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Kullanıcıyı oluştur
    hashed_password = auth_service.get_password_hash(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Kullanıcıyı veritabanına ekle
    result = await auth_service.db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    # Token oluştur
    access_token = auth_service.create_access_token(
        data={"sub": user_data.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Kullanıcı girişi"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token oluştur
    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    return UserResponse(**{**current_user.dict(), "_id": current_user.id})
