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


@router.post("/{content_id}", response_model=CommentResponse)
async def create_comment(
    content_id: str,
    comment: CommentCreate,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriğe yorum ekler"""
    user = await auth_service.get_user_from_token(authorization)
    return await comment_service.create_comment(
        content_id=content_id, comment=comment, user_id=str(user.id)
    )


@router.get("/{content_id}", response_model=List[CommentResponse])
async def get_comments(
    content_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """İçeriğin yorumlarını getirir"""
    return await comment_service.get_comments(
        content_id=content_id, skip=skip, limit=limit
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: UserInDB = Depends(auth_service.get_current_user),
):
    """Yorumu günceller"""
    return await comment_service.update_comment(
        comment_id=comment_id, comment_update=comment_update, user_id=current_user.id
    )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: UserInDB = Depends(auth_service.get_current_user),
):
    """Yorumu siler"""
    return await comment_service.delete_comment(
        comment_id=comment_id, user_id=current_user.id
    )


@router.get("/user/me", response_model=List[CommentResponse])
async def get_user_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserInDB = Depends(auth_service.get_current_user),
):
    """Kullanıcının kendi yorumlarını getirir"""
    return await comment_service.get_user_comments(
        user_id=current_user.id, skip=skip, limit=limit
    )
