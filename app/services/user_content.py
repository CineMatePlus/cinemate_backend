from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user_content import (
    UserContentCreate,
    UserContentUpdate,
    UserContentInDB,
)
from app.db.mongodb import get_database


class UserContentService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()

    async def get_or_create_user_content(
        self, user_id: str, content_id: str
    ) -> UserContentInDB:
        """Kullanıcı-içerik ilişkisini getirir veya oluşturur"""
        try:
            user_content = await self.db.user_contents.find_one(
                {"user_id": ObjectId(user_id), "content_id": ObjectId(content_id)}
            )
            if not user_content:
                user_content = {
                    "user_id": ObjectId(user_id),
                    "content_id": ObjectId(content_id),
                    "is_watched": False,
                    "is_liked": False,
                    "rating": None,
                }
                result = await self.db.user_contents.insert_one(user_content)
                user_content["_id"] = result.inserted_id
            return UserContentInDB(**{**user_content, "_id": str(user_content["_id"])})
        except Exception as e:
            raise ValueError(
                f"Kullanıcı-içerik ilişkisi getirilirken hata oluştu: {str(e)}"
            )

    async def mark_as_watched(
        self, user_id: str, content_id: str, is_watched: bool
    ) -> UserContentInDB:
        """İçeriği izlendi/izlenmedi olarak işaretler"""
        try:
            user_content = await self.get_or_create_user_content(user_id, content_id)
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {"$set": {"is_watched": is_watched}},
            )
            updated_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            return UserContentInDB(
                **{**updated_content, "_id": str(updated_content["_id"])}
            )
        except Exception as e:
            raise ValueError(f"İzleme durumu güncellenirken hata oluştu: {str(e)}")

    async def like_content(
        self, user_id: str, content_id: str, is_liked: bool
    ) -> UserContentInDB:
        """İçeriği beğenir/beğenmez"""
        try:
            user_content = await self.get_or_create_user_content(user_id, content_id)
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {"$set": {"is_liked": is_liked}},
            )
            updated_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            return UserContentInDB(
                **{**updated_content, "_id": str(updated_content["_id"])}
            )
        except Exception as e:
            raise ValueError(f"Beğeni durumu güncellenirken hata oluştu: {str(e)}")

    async def rate_content(
        self, user_id: str, content_id: str, rating: int
    ) -> UserContentInDB:
        """İçeriğe puan verir"""
        try:
            if not 1 <= rating <= 10:
                raise ValueError("Puan 1-10 arasında olmalıdır")

            user_content = await self.get_or_create_user_content(user_id, content_id)
            await self.db.user_contents.update_one(
                {"_id": ObjectId(user_content.id)},
                {"$set": {"rating": rating}},
            )
            updated_content = await self.db.user_contents.find_one(
                {"_id": ObjectId(user_content.id)}
            )
            return UserContentInDB(
                **{**updated_content, "_id": str(updated_content["_id"])}
            )
        except Exception as e:
            raise ValueError(f"Puan güncellenirken hata oluştu: {str(e)}")

    async def get_user_contents(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[UserContentInDB]:
        """Kullanıcının tüm içerik ilişkilerini getirir"""
        try:
            user_contents = (
                await self.db.user_contents.find({"user_id": ObjectId(user_id)})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            return [
                UserContentInDB(**{**content, "_id": str(content["_id"])})
                for content in user_contents
            ]
        except Exception as e:
            raise ValueError(f"Kullanıcı içerikleri getirilirken hata oluştu: {str(e)}")

    async def get_content_stats(self, content_id: str) -> dict:
        """İçeriğin istatistiklerini getirir"""
        try:
            stats = {
                "total_watched": await self.db.user_contents.count_documents(
                    {"content_id": ObjectId(content_id), "is_watched": True}
                ),
                "total_likes": await self.db.user_contents.count_documents(
                    {"content_id": ObjectId(content_id), "is_liked": True}
                ),
                "average_rating": 0.0,
            }

            # Ortalama puanı hesapla
            ratings = await self.db.user_contents.find(
                {"content_id": ObjectId(content_id), "rating": {"$ne": None}},
                {"rating": 1},
            ).to_list(length=None)

            if ratings:
                total_rating = sum(r["rating"] for r in ratings)
                stats["average_rating"] = round(total_rating / len(ratings), 1)

            return stats
        except Exception as e:
            raise ValueError(
                f"İçerik istatistikleri getirilirken hata oluştu: {str(e)}"
            )
