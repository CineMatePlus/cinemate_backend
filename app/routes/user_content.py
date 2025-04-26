from fastapi import APIRouter, Query, Header
from typing import List
from app.models.user_content import UserContentResponse
from app.models.content import ContentResponse
from app.services.user_content import UserContentService
from app.services.auth import AuthService

router = APIRouter(tags=["user-contents"])

# Servis örneği
user_content_service = UserContentService()
auth_service = AuthService()


@router.get("/{content_id}/status", response_model=UserContentResponse)
async def get_user_content_status(
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının belirli bir içerik ile ilgili durumunu getirir"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.get_user_content_status(
        content_id=content_id, user_id=str(user.id)
    )


@router.post("/{content_id}/like", response_model=UserContentResponse)
async def like_content(
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği beğenir veya beğenmeyi kaldırır"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.like_content(
        content_id=content_id, user_id=str(user.id)
    )


@router.post("/{content_id}/watch", response_model=UserContentResponse)
async def mark_as_watched(
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği izlendi olarak işaretler veya işareti kaldırır"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.mark_as_watched(
        content_id=content_id, user_id=str(user.id)
    )


@router.post("/{content_id}/watchlist", response_model=UserContentResponse)
async def toggle_watchlist(
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği izleme listesine ekler veya çıkarır"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.toggle_watchlist(
        content_id=content_id, user_id=str(user.id)
    )


@router.post("/{content_id}/rate", response_model=UserContentResponse)
async def rate_content(
    content_id: str,
    rating: int = Query(..., ge=1, le=5),
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği puanlar"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.rate_content(
        content_id=content_id, user_id=str(user.id), rating=rating
    )


@router.get("/watch-history", response_model=List[ContentResponse])
async def get_watch_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının izleme geçmişini getirir"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.get_watch_history(
        user_id=str(user.id), skip=skip, limit=limit
    )


@router.get("/watchlist", response_model=List[ContentResponse])
async def get_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının izleme listesini getirir"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.get_watchlist(
        user_id=str(user.id), skip=skip, limit=limit
    )


@router.get("/liked", response_model=List[ContentResponse])
async def get_liked_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının beğendiği içerikleri getirir"""
    user = await auth_service.get_user_from_token(authorization)
    return await user_content_service.get_liked_contents(
        user_id=str(user.id), skip=skip, limit=limit
    )
