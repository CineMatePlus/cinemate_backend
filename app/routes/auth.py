from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserInDB, UserResponse
from app.models.auth import Token, RegisterRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# Servis örneği
auth_service = AuthService()


@router.post("/register", response_model=Token)
async def register(user_data: RegisterRequest):
    """Yeni kullanıcı kaydı"""
    return await auth_service.register_user(user_data.dict())


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Kullanıcı girişi"""
    return await auth_service.login_user(form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    return UserResponse(**{**current_user.dict(), "_id": current_user.id})
