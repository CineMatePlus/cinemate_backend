from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user_content import (
    UserContentCreate,
    UserContentUpdate,
    UserContentInDB,
    UserContentResponse,
)
from app.db.mongodb import get_database


class UserContentService:
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

    async def get_or_create_user_content(
        self, user_id: str, content_id: str
    ) -> UserContentInDB:
        """Kullanıcı-İçerik ilişkisini getirir veya oluşturur"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            user_content = await self.db.user_contents.find_one(
                {"user_id": user_id, "content_id": str(content_object_id)}
            )

            if not user_content:
                user_content = {
                    "user_id": user_id,
                    "content_id": str(content_object_id),
                    "is_liked": False,
                    "is_watched": False,
                    "in_watchlist": False,
                    "rated": None,
                    "last_interacted_at": datetime.utcnow(),
                }
                result = await self.db.user_contents.insert_one(user_content)
                user_content["_id"] = str(result.inserted_id)
                return UserContentInDB(**user_content)

            user_content["_id"] = str(user_content["_id"])
            return UserContentInDB(**user_content)
        except Exception as e:
            self._handle_exception(e)

    async def like_content(self, content_id: str, user_id: str) -> UserContentResponse:
        """İçeriği beğenir veya beğenmeyi kaldırır"""
        try:
            # İçeriğin var olduğunu kontrol et
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            # Kullanıcı-İçerik ilişkisini getir
            user_content = await self.get_or_create_user_content(
                user_id, str(content_object_id)
            )

            # Beğeni durumunu tersine çevir
            new_like_status = not user_content.is_liked

            # İlişkiyi güncelle
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {
                    "$set": {
                        "is_liked": new_like_status,
                        "last_interacted_at": datetime.utcnow(),
                    }
                },
            )

            # İçerikteki beğeni sayısını güncelle
            await self.db.contents.update_one(
                {"_id": content_object_id},
                {"$inc": {"num_likes": 1 if new_like_status else -1}},
            )

            # Güncellenmiş ilişkiyi dön
            updated_user_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            if not updated_user_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Güncellenmiş kullanıcı içeriği alınamadı",
                )

            updated_user_content["_id"] = str(updated_user_content["_id"])
            return UserContentResponse(**updated_user_content)
        except Exception as e:
            self._handle_exception(e)

    async def mark_as_watched(
        self, content_id: str, user_id: str
    ) -> UserContentResponse:
        """İçeriği izlendi olarak işaretler veya işareti kaldırır"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            user_content = await self.get_or_create_user_content(
                user_id, str(content_object_id)
            )

            # İzlenme durumunu tersine çevir
            new_watched_status = not user_content.is_watched

            # İlişkiyi güncelle
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {
                    "$set": {
                        "is_watched": new_watched_status,
                        "last_interacted_at": datetime.utcnow(),
                    }
                },
            )

            # İçerikteki izlenme sayısını güncelle
            await self.db.contents.update_one(
                {"_id": content_object_id},
                {"$inc": {"num_watches": 1 if new_watched_status else -1}},
            )

            updated_user_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            if not updated_user_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Güncellenmiş kullanıcı içeriği alınamadı",
                )

            updated_user_content["_id"] = str(updated_user_content["_id"])
            return UserContentResponse(**updated_user_content)
        except Exception as e:
            self._handle_exception(e)

    async def toggle_watchlist(
        self, content_id: str, user_id: str
    ) -> UserContentResponse:
        """İçeriği izleme listesine ekler veya çıkarır"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            user_content = await self.get_or_create_user_content(
                user_id, str(content_object_id)
            )
            new_watchlist_status = not user_content.in_watchlist

            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {
                    "$set": {
                        "in_watchlist": new_watchlist_status,
                        "last_interacted_at": datetime.utcnow(),
                    }
                },
            )

            updated_user_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            if not updated_user_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Güncellenmiş kullanıcı içeriği alınamadı",
                )

            updated_user_content["_id"] = str(updated_user_content["_id"])
            return UserContentResponse(**updated_user_content)
        except Exception as e:
            self._handle_exception(e)

    async def rate_content(
        self, content_id: str, user_id: str, rating: int
    ) -> UserContentResponse:
        """İçeriği puanlar"""
        try:
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            user_content = await self.get_or_create_user_content(
                user_id, str(content_object_id)
            )

            # Eski puanı al
            old_rating = user_content.rated or 0

            # İlişkiyi güncelle
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {"$set": {"rated": rating, "last_interacted_at": datetime.utcnow()}},
            )

            # İçeriğin ortalama puanını güncelle
            content["_id"] = str(content["_id"])
            total_ratings = content.get("num_ratings", 0)
            current_avg = content.get("average_rating", 0.0)

            if old_rating == 0:  # İlk puanlama
                if total_ratings == 0:
                    new_avg = float(rating)
                else:
                    new_avg = (current_avg * total_ratings + float(rating)) / (
                        total_ratings + 1
                    )
                await self.db.contents.update_one(
                    {"_id": content_object_id},
                    {"$set": {"average_rating": new_avg}, "$inc": {"num_ratings": 1}},
                )
            else:  # Puan güncelleme
                if total_ratings == 0:
                    new_avg = float(rating)
                else:
                    new_avg = (
                        current_avg * total_ratings - float(old_rating) + float(rating)
                    ) / total_ratings
                await self.db.contents.update_one(
                    {"_id": content_object_id}, {"$set": {"average_rating": new_avg}}
                )

            updated_user_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            if not updated_user_content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Güncellenmiş kullanıcı içeriği alınamadı",
                )

            updated_user_content["_id"] = str(updated_user_content["_id"])
            return UserContentResponse(**updated_user_content)
        except Exception as e:
            self._handle_exception(e)

    async def get_watch_history(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[UserContentResponse]:
        """Kullanıcının izleme geçmişini getirir"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "is_watched": True}},
                {"$addFields": {"content_id_obj": {"$toObjectId": "$content_id"}}},
                {
                    "$lookup": {
                        "from": "contents",
                        "localField": "content_id_obj",
                        "foreignField": "_id",
                        "as": "content",
                    }
                },
                {"$unwind": {"path": "$content", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "user_id": 1,
                        "content_id": 1,
                        "is_liked": 1,
                        "is_watched": 1,
                        "in_watchlist": 1,
                        "rated": 1,
                        "last_interacted_at": 1,
                        "content": {"title": 1, "num_likes": 1, "year": 1},
                    }
                },
                {"$sort": {"last_interacted_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            user_contents = await self.db.user_contents.aggregate(pipeline).to_list(
                length=limit
            )

            return [UserContentResponse(**uc) for uc in user_contents]
        except Exception as e:
            self._handle_exception(e)

    async def get_watchlist(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[UserContentResponse]:
        """Kullanıcının izleme listesini getirir"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "in_watchlist": True}},
                {"$addFields": {"content_id_obj": {"$toObjectId": "$content_id"}}},
                {
                    "$lookup": {
                        "from": "contents",
                        "localField": "content_id_obj",
                        "foreignField": "_id",
                        "as": "content",
                    }
                },
                {"$unwind": {"path": "$content", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "user_id": 1,
                        "content_id": 1,
                        "is_liked": 1,
                        "is_watched": 1,
                        "in_watchlist": 1,
                        "rated": 1,
                        "last_interacted_at": 1,
                        "content": {"title": 1, "num_likes": 1, "year": 1},
                    }
                },
                {"$sort": {"last_interacted_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            user_contents = await self.db.user_contents.aggregate(pipeline).to_list(
                length=limit
            )

            return [UserContentResponse(**uc) for uc in user_contents]
        except Exception as e:
            self._handle_exception(e)

    async def get_liked_contents(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[UserContentResponse]:
        """Kullanıcının beğendiği içerikleri getirir"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "is_liked": True}},
                {"$addFields": {"content_id_obj": {"$toObjectId": "$content_id"}}},
                {
                    "$lookup": {
                        "from": "contents",
                        "localField": "content_id_obj",
                        "foreignField": "_id",
                        "as": "content",
                    }
                },
                {"$unwind": {"path": "$content", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "user_id": 1,
                        "content_id": 1,
                        "is_liked": 1,
                        "is_watched": 1,
                        "in_watchlist": 1,
                        "rated": 1,
                        "last_interacted_at": 1,
                        "content": {"title": 1, "num_likes": 1, "year": 1},
                    }
                },
                {"$sort": {"last_interacted_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            user_contents = await self.db.user_contents.aggregate(pipeline).to_list(
                length=limit
            )

            return [UserContentResponse(**uc) for uc in user_contents]
        except Exception as e:
            self._handle_exception(e)
