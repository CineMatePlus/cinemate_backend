from fastapi import APIRouter, Depends, Query, Header
from typing import List
from app.models.comment import (
    CommentResponse,
    CommentCreate,
    CommentUpdate,
)
from app.services.comment import CommentService
from app.services.auth import AuthService
from app.models.user import UserInDB

router = APIRouter(tags=["comments"])

# Servis örneği
comment_service = CommentService()
auth_service = AuthService()


@router.post("/{movie_id}", response_model=CommentResponse)
async def create_comment(
    movie_id: str,
    comment: CommentCreate,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriğe yorum ekler"""
    user = await auth_service.get_user_from_token(authorization)
    return await comment_service.create_comment(
        movie_id=movie_id, comment=comment, user_id=str(user.id)
    )


@router.get("/{movie_id}", response_model=List[CommentResponse])
async def get_comments(
    movie_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """İçeriğin yorumlarını getirir"""
    return await comment_service.get_comments(
        movie_id=movie_id, skip=skip, limit=limit
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    authorization: str = Header(..., description="Bearer token"),
):
    """Yorumu günceller"""
    user = await auth_service.get_user_from_token(authorization)
    return await comment_service.update_comment(
        comment_id=comment_id, comment_update=comment_update, user_id=str(user.id)
    )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Yorumu siler"""
    user = await auth_service.get_user_from_token(authorization)
    return await comment_service.delete_comment(
        comment_id=comment_id, user_id=str(user.id)
    )


@router.get("/user/me", response_model=List[CommentResponse])
async def get_user_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının kendi yorumlarını getirir"""
    user = await auth_service.get_user_from_token(authorization)
    return await comment_service.get_user_comments(
        user_id=str(user.id), skip=skip, limit=limit
    )
