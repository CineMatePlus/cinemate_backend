from fastapi import APIRouter, Depends, Query
from typing import List
from app.models.user_content import UserContentResponse
from app.services.user_content import UserContentService
from app.services.auth import AuthService
from app.models.user import UserInDB

router = APIRouter(prefix="/user-content", tags=["user-contents"])

# Servis örneği
user_content_service = UserContentService()
auth_service = AuthService()


@router.post("/{content_id}/like", response_model=UserContentResponse)
async def like_content(
    content_id: str,
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği beğenir veya beğenmeyi kaldırır"""
    return await user_content_service.like_content(
        content_id=content_id, user_id=str(current_user.id)
    )


@router.post("/{content_id}/watch", response_model=UserContentResponse)
async def mark_as_watched(
    content_id: str,
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği izlendi olarak işaretler veya işareti kaldırır"""
    return await user_content_service.mark_as_watched(
        content_id=content_id, user_id=str(current_user.id)
    )


@router.post("/{content_id}/watchlist", response_model=UserContentResponse)
async def toggle_watchlist(
    content_id: str,
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği izleme listesine ekler veya çıkarır"""
    return await user_content_service.toggle_watchlist(
        content_id=content_id, user_id=str(current_user.id)
    )


@router.post("/{content_id}/rate", response_model=UserContentResponse)
async def rate_content(
    content_id: str,
    rating: int = Query(..., ge=1, le=10),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği puanlar"""
    return await user_content_service.rate_content(
        content_id=content_id, user_id=str(current_user.id), rating=rating
    )


@router.get("/history", response_model=List[UserContentResponse])
async def get_watch_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """Kullanıcının izleme geçmişini getirir"""
    return await user_content_service.get_watch_history(
        user_id=str(current_user.id), skip=skip, limit=limit
    )


@router.get("/watchlist", response_model=List[UserContentResponse])
async def get_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """Kullanıcının izleme listesini getirir"""
    return await user_content_service.get_watchlist(
        user_id=str(current_user.id), skip=skip, limit=limit
    )


@router.get("/liked", response_model=List[UserContentResponse])
async def get_liked_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """Kullanıcının beğendiği içerikleri getirir"""
    return await user_content_service.get_liked_contents(
        user_id=str(current_user.id), skip=skip, limit=limit
    )
