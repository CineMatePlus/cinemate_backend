from fastapi import APIRouter, Depends, Query, Header
from typing import List, Optional
from app.models.content import (
    ContentResponse,
    ContentCreate,
    ContentUpdate,
)
from app.services.content import ContentService
from app.services.auth import AuthService
from app.models.user import UserInDB

router = APIRouter(tags=["contents"])

# Servis örneği
content_service = ContentService()
auth_service = AuthService()


@router.get("", response_model=List[ContentResponse])
async def list_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    type: Optional[bool] = None,
):
    """İçerikleri listeler ve filtreler"""
    return await content_service.list_contents(
        skip=skip, limit=limit, genre=genre, year=year, type=type
    )


@router.get("/search", response_model=List[ContentResponse])
async def search_contents(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    type: Optional[bool] = None,
):
    """İçeriklerde arama yapar"""
    return await content_service.search_contents(query=query, skip=skip, limit=limit, type=type)


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    """Belirli bir içeriğin detaylarını getirir"""
    return await content_service.get_content(content_id=content_id)


@router.post("/", response_model=ContentResponse)
async def create_content(
    content: ContentCreate,
    authorization: str = Header(..., description="Bearer token"),
):
    """Yeni içerik oluşturur"""
    await auth_service.get_user_from_token(authorization)
    return await content_service.create_content(content=content)


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği günceller"""
    await auth_service.get_user_from_token(authorization)
    return await content_service.update_content(
        content_id=content_id, content_update=content_update
    )


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """İçeriği siler"""
    await auth_service.get_user_from_token(authorization)
    return await content_service.delete_content(content_id=content_id)
