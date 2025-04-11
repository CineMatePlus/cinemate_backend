from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.content import ContentCreate, ContentUpdate, ContentInDB
from app.db.mongodb import get_database


class ContentService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()

    async def create_content(self, content: ContentCreate) -> ContentInDB:
        """Yeni içerik oluşturur"""
        try:
            content_dict = content.dict()
            result = await self.db.contents.insert_one(content_dict)
            created_content = await self.db.contents.find_one(
                {"_id": result.inserted_id}
            )
            return ContentInDB(
                **{**created_content, "_id": str(created_content["_id"])}
            )
        except Exception as e:
            raise ValueError(f"İçerik oluşturulurken hata oluştu: {str(e)}")

    async def get_content(self, content_id: str) -> Optional[ContentInDB]:
        """Belirli bir içeriği getirir"""
        try:
            content = await self.db.contents.find_one({"_id": ObjectId(content_id)})
            if content:
                return ContentInDB(**{**content, "_id": str(content["_id"])})
            return None
        except Exception as e:
            raise ValueError(f"İçerik getirilirken hata oluştu: {str(e)}")

    async def get_contents(
        self, skip: int = 0, limit: int = 10, search: Optional[str] = None
    ) -> List[ContentInDB]:
        """Tüm içerikleri getirir"""
        try:
            query = {}
            if search:
                query = {
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},
                        {"description": {"$regex": search, "$options": "i"}},
                    ]
                }

            contents = (
                await self.db.contents.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            return [
                ContentInDB(**{**content, "_id": str(content["_id"])})
                for content in contents
            ]
        except Exception as e:
            raise ValueError(f"İçerikler getirilirken hata oluştu: {str(e)}")

    async def update_content(
        self, content_id: str, content_update: ContentUpdate
    ) -> ContentInDB:
        """İçeriği günceller"""
        try:
            content = await self.db.contents.find_one({"_id": ObjectId(content_id)})
            if not content:
                raise ValueError("İçerik bulunamadı")

            update_data = content_update.dict(exclude_unset=True)
            await self.db.contents.update_one(
                {"_id": ObjectId(content_id)}, {"$set": update_data}
            )
            updated_content = await self.db.contents.find_one(
                {"_id": ObjectId(content_id)}
            )
            return ContentInDB(
                **{**updated_content, "_id": str(updated_content["_id"])}
            )
        except Exception as e:
            raise ValueError(f"İçerik güncellenirken hata oluştu: {str(e)}")

    async def delete_content(self, content_id: str) -> bool:
        """İçeriği siler"""
        try:
            content = await self.db.contents.find_one({"_id": ObjectId(content_id)})
            if not content:
                raise ValueError("İçerik bulunamadı")

            result = await self.db.contents.delete_one({"_id": ObjectId(content_id)})
            return result.deleted_count > 0
        except Exception as e:
            raise ValueError(f"İçerik silinirken hata oluştu: {str(e)}")
