from fastapi import APIRouter, Header
from app.models.auth import RegisterRequest, LoginRequest, AuthResponse
from app.models.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(tags=["auth"])

# Servis örneği
auth_service = AuthService()


@router.post("/register", response_model=AuthResponse)
async def register(user_data: RegisterRequest):
    """Yeni kullanıcı kaydı"""
    return await auth_service.register_user(user_data.dict())


@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """Kullanıcı girişi"""
    return await auth_service.login_user(
        username=login_data.email,
        password=login_data.password
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    authorization: str = Header(..., description="Bearer token")
):
    """Mevcut kullanıcı bilgilerini getir"""
    return await auth_service.get_user_from_token(authorization)


# TODO: Token response dönebilir
@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    authorization: str = Header(..., description="Bearer token")
):
    """Token yenileme"""
    return await auth_service.refresh_token(authorization)
