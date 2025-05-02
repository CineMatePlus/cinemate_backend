from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from typing import List
from bson import ObjectId
from app.models.collection import (
    CollectionResponse,
    CollectionCreate,
    CollectionUpdate,
)
from app.services.collection import CollectionService
from app.services.auth import AuthService
from app.models.user import UserInDB

router = APIRouter(tags=["collections"])

# Servis örneği
collection_service = CollectionService()
auth_service = AuthService()


@router.post("/", response_model=CollectionResponse)
async def create_collection(
    collection: CollectionCreate,
    authorization: str = Header(..., description="Bearer token"),
):
    """Yeni koleksiyon oluşturur"""
    user = await auth_service.get_user_from_token(authorization)
    created_collection = await collection_service.create_collection(
        collection=collection, user_id=str(user.id)
    )
    return CollectionResponse(
        **{**created_collection.dict(), "_id": str(created_collection.id)}
    )


@router.get("/", response_model=List[CollectionResponse])
async def get_user_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: str = Header(..., description="Bearer token"),
):
    """Kullanıcının koleksiyonlarını getirir"""
    user = await auth_service.get_user_from_token(authorization)
    collections = await collection_service.get_collections(
        user_id=str(user.id), skip=skip, limit=limit
    )
    return [
        CollectionResponse(**{**collection.dict(), "_id": str(collection.id)})
        for collection in collections
    ]


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Koleksiyon detaylarını getirir"""
    user = await auth_service.get_user_from_token(authorization)
    collection = await collection_service.get_collection(collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Koleksiyon bulunamadı"
        )
    if collection.user_id != str(user.id) and not collection.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu koleksiyonu görüntüleme yetkiniz yok",
        )
    return CollectionResponse(**{**collection.dict(), "_id": str(collection.id)})


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection_update: CollectionUpdate,
    authorization: str = Header(..., description="Bearer token"),
):
    """Koleksiyonu günceller"""
    user = await auth_service.get_user_from_token(authorization)
    updated_collection = await collection_service.update_collection(
        collection_id=collection_id,
        collection=collection_update,
        user_id=str(user.id),
    )
    return CollectionResponse(
        **{**updated_collection.dict(), "_id": str(updated_collection.id)}
    )


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Koleksiyonu siler"""
    user = await auth_service.get_user_from_token(authorization)
    await collection_service.delete_collection(
        collection_id=collection_id, user_id=str(user.id)
    )
    return {"message": "Koleksiyon başarıyla silindi"}


@router.post("/{collection_id}/contents/{content_id}")
async def add_content_to_collection(
    collection_id: str,
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Koleksiyona içerik ekler"""
    user = await auth_service.get_user_from_token(authorization)
    await collection_service.add_content_to_collection(
        collection_id=collection_id,
        content_id=content_id,
        user_id=str(user.id),
    )
    return {"message": "İçerik koleksiyona başarıyla eklendi"}


@router.delete("/{collection_id}/contents/{content_id}")
async def remove_content_from_collection(
    collection_id: str,
    content_id: str,
    authorization: str = Header(..., description="Bearer token"),
):
    """Koleksiyondan içerik çıkarır"""
    user = await auth_service.get_user_from_token(authorization)
    await collection_service.remove_content_from_collection(
        collection_id=collection_id,
        content_id=content_id,
        user_id=str(user.id),
    )
    return {"message": "İçerik koleksiyondan başarıyla çıkarıldı"}


@router.get("/user/{user_id}", response_model=List[CollectionResponse])
async def get_user_public_collections(
    user_id: str, skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)
):
    """Kullanıcının public koleksiyonlarını getirir"""
    collections = await collection_service.get_public_collections(
        user_id=user_id, skip=skip, limit=limit
    )
    return [
        CollectionResponse(**{**collection.dict(), "_id": str(collection.id)})
        for collection in collections
    ]
