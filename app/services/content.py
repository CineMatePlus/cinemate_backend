from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.content import (
    ContentCreate,
    ContentUpdate,
    ContentListResponse,
    ContentResponse,
)
from app.db.mongodb import get_database


class ContentService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()

    def _convert_to_object_id(self, id_str: str) -> ObjectId:
        """String ID'yi ObjectId'ye dönüştürür"""
        try:
            return ObjectId(id_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz ID formatı: {id_str}",
            )

    def _handle_exception(self, e: Exception) -> None:
        """Hata yakalama ve HTTPException fırlatma"""
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz veri: {str(e)}",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bir hata oluştu: {str(e)}",
        )

    async def list_contents(
        self,
        skip: int = 0,
        limit: int = 10,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        type: Optional[bool] = None,
    ) -> List[ContentListResponse]:
        """İçerikleri listeler ve filtreler"""
        try:
            query = {}
            if genre:
                query["genres"] = genre
            if year:
                query["year"] = year
            if type is not None:
                query["type"] = type

            pipeline = [
                {"$match": query},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "title": 1,
                        "year": 1,
                        "genres": 1,
                        "num_likes": 1,
                        "average_rating": 1,
                        "type": 1,
                    }
                },
                {"$skip": skip},
                {"$limit": limit},
            ]

            contents = await self.db.contents.aggregate(pipeline).to_list(length=limit)
            return [ContentListResponse(**content) for content in contents]
        except Exception as e:
            self._handle_exception(e)

    async def get_content(self, content_id: str) -> ContentResponse:
        """Belirli bir içeriğin detaylarını getirir"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )
            content["_id"] = str(content["_id"])
            return ContentResponse(**content)
        except Exception as e:
            self._handle_exception(e)

    async def create_content(self, content: ContentCreate) -> ContentResponse:
        """Yeni içerik oluşturur"""
        try:
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

            result = await self.db.contents.insert_one(content_dict)
            content_dict["_id"] = str(result.inserted_id)

            return ContentResponse(**content_dict)
        except Exception as e:
            self._handle_exception(e)

    async def update_content(
        self, content_id: str, content_update: ContentUpdate
    ) -> ContentResponse:
        """İçeriği günceller"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            update_data = content_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            await self.db.contents.update_one(
                {"_id": content_object_id}, {"$set": update_data}
            )

            updated_content = await self.db.contents.find_one(
                {"_id": content_object_id}
            )
            updated_content["_id"] = str(updated_content["_id"])
            return ContentResponse(**updated_content)
        except Exception as e:
            self._handle_exception(e)

    async def delete_content(self, content_id: str) -> dict:
        """İçeriği siler"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            result = await self.db.contents.delete_one({"_id": content_object_id})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )
            return {"message": "İçerik başarıyla silindi"}
        except Exception as e:
            self._handle_exception(e)

    async def search_contents(
        self, query: str, skip: int = 0, limit: int = 10, type: Optional[bool] = None
    ) -> List[ContentListResponse]:
        """İçeriklerde arama yapar"""
        try:
            match_query = {"$text": {"$search": query}}
            if type is not None:
                match_query["type"] = type
                
            pipeline = [
                {"$match": match_query},
                {"$addFields": {"score": {"$meta": "textScore"}}},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "title": 1,
                        "year": 1,
                        "genres": 1,
                        "num_likes": 1,
                        "average_rating": 1,
                        "type": 1,
                        "score": 1,
                    }
                },
                {"$sort": {"score": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            contents = await self.db.contents.aggregate(pipeline).to_list(length=limit)
            return [ContentListResponse(**content) for content in contents]
        except Exception as e:
            self._handle_exception(e)
