from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.content import (
    ContentResponse,
    ContentCreate,
    ContentUpdate,
)
from app.db.mongodb import get_database
from app.services.auth import AuthService
from app.models.user import UserInDB
from datetime import datetime
from app.services.content import ContentService

router = APIRouter(prefix="/contents", tags=["contents"])

# Servis örneği
content_service = ContentService()
auth_service = AuthService()


@router.get("/", response_model=List[ContentResponse])
async def list_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """İçerikleri listeler ve filtreler"""
    query = {}
    if genre:
        query["genres"] = genre
    if year:
        query["year"] = year

    contents = (
        await db.contents.find(query).skip(skip).limit(limit).to_list(length=limit)
    )
    # ObjectId'leri string'e çevir
    contents = [{**content, "_id": str(content["_id"])} for content in contents]
    return [ContentResponse(**content) for content in contents]


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Belirli bir içeriğin detaylarını getirir"""
    try:
        # String ID'yi ObjectId'ye çevir
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        content["_id"] = str(content["_id"])
        return ContentResponse(**content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )


@router.post("/", response_model=ContentResponse)
async def create_content(
    content: ContentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """Yeni içerik oluşturur"""
    content_dict = content.dict()
    content_dict.update(
        {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "average_rating": 0.0,
            "num_likes": 0,
            "num_watches": 0,
            "num_ratings": 0,
            "num_comments": 0,
        }
    )

    result = await db.contents.insert_one(content_dict)
    content_dict["_id"] = str(result.inserted_id)

    return ContentResponse(**content_dict)


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği günceller"""
    try:
        # String ID'yi ObjectId'ye çevir
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        update_data = content_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await db.contents.update_one({"_id": object_id}, {"$set": update_data})

        updated_content = await db.contents.find_one({"_id": object_id})
        updated_content["_id"] = str(updated_content["_id"])
        return ContentResponse(**updated_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(auth_service.get_current_active_user),
):
    """İçeriği siler"""
    try:
        # String ID'yi ObjectId'ye çevir
        object_id = ObjectId(content_id)
        result = await db.contents.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        return {"message": "Content deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )


@router.get("/search/", response_model=List[ContentResponse])
async def search_contents(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """İçeriklerde arama yapar"""
    contents = (
        await db.contents.find(
            {"$text": {"$search": query}}, {"score": {"$meta": "textScore"}}
        )
        .sort([("score", {"$meta": "textScore"})])
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    # ObjectId'leri string'e çevir
    contents = [{**content, "_id": str(content["_id"])} for content in contents]
    return [ContentResponse(**content) for content in contents]
