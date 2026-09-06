from fastapi import APIRouter, Header, Response, status

from app.models.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.models.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(tags=["auth"])
auth_service = AuthService()


async def _authenticated_user(authorization: str):
    token = auth_service.bearer_token(authorization)
    return await auth_service.get_current_user(token)


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: RegisterRequest):
    return await auth_service.register_user(user_data.model_dump())


@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    return await auth_service.login_user(
        username=str(login_data.email), password=login_data.password
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(authorization: str = Header(..., description="Bearer token")):
    return await auth_service.get_user_from_token(authorization)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshRequest):
    return await auth_service.refresh_token(request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: LogoutRequest) -> Response:
    await auth_service.logout(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    authorization: str = Header(..., description="Bearer access token"),
) -> Response:
    await auth_service.logout_all(await _authenticated_user(authorization))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    authorization: str = Header(..., description="Bearer access token"),
) -> Response:
    await auth_service.change_password(
        await _authenticated_user(authorization),
        request.current_password,
        request.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
