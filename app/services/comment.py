from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.comment import CommentCreate, CommentUpdate, CommentInDB
from app.db.mongodb import get_database


class CommentService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or get_database()

    async def create_comment(self, comment: CommentCreate, user_id: str) -> CommentInDB:
        """Yeni yorum oluşturur"""
        try:
            comment_dict = comment.dict()
            comment_dict["user_id"] = user_id
            result = await self.db.comments.insert_one(comment_dict)
            created_comment = await self.db.comments.find_one(
                {"_id": result.inserted_id}
            )
            return CommentInDB(
                **{**created_comment, "_id": str(created_comment["_id"])}
            )
        except Exception as e:
            raise ValueError(f"Yorum oluşturulurken hata oluştu: {str(e)}")

    async def get_comments(
        self, content_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentInDB]:
        """İçeriğin yorumlarını getirir"""
        try:
            comments = (
                await self.db.comments.find({"content_id": content_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            return [
                CommentInDB(**{**comment, "_id": str(comment["_id"])})
                for comment in comments
            ]
        except Exception as e:
            raise ValueError(f"Yorumlar getirilirken hata oluştu: {str(e)}")

    async def get_comment(self, comment_id: str) -> Optional[CommentInDB]:
        """Belirli bir yorumu getirir"""
        try:
            comment = await self.db.comments.find_one({"_id": ObjectId(comment_id)})
            if comment:
                return CommentInDB(**{**comment, "_id": str(comment["_id"])})
            return None
        except Exception as e:
            raise ValueError(f"Yorum getirilirken hata oluştu: {str(e)}")

    async def update_comment(
        self, comment_id: str, comment_update: CommentUpdate, user_id: str
    ) -> CommentInDB:
        """Yorumu günceller"""
        try:
            comment = await self.db.comments.find_one({"_id": ObjectId(comment_id)})
            if not comment:
                raise ValueError("Yorum bulunamadı")
            if comment["user_id"] != user_id:
                raise ValueError("Bu yorumu güncelleme yetkiniz yok")

            update_data = comment_update.dict(exclude_unset=True)
            await self.db.comments.update_one(
                {"_id": ObjectId(comment_id)}, {"$set": update_data}
            )
            updated_comment = await self.db.comments.find_one(
                {"_id": ObjectId(comment_id)}
            )
            return CommentInDB(
                **{**updated_comment, "_id": str(updated_comment["_id"])}
            )
        except Exception as e:
            raise ValueError(f"Yorum güncellenirken hata oluştu: {str(e)}")

    async def delete_comment(self, comment_id: str, user_id: str) -> bool:
        """Yorumu siler"""
        try:
            comment = await self.db.comments.find_one({"_id": ObjectId(comment_id)})
            if not comment:
                raise ValueError("Yorum bulunamadı")
            if comment["user_id"] != user_id:
                raise ValueError("Bu yorumu silme yetkiniz yok")

            result = await self.db.comments.delete_one({"_id": ObjectId(comment_id)})
            return result.deleted_count > 0
        except Exception as e:
            raise ValueError(f"Yorum silinirken hata oluştu: {str(e)}")

    async def get_user_comments(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentInDB]:
        """Kullanıcının yorumlarını getirir"""
        try:
            comments = (
                await self.db.comments.find({"user_id": user_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )
            return [
                CommentInDB(**{**comment, "_id": str(comment["_id"])})
                for comment in comments
            ]
        except Exception as e:
            raise ValueError(f"Kullanıcı yorumları getirilirken hata oluştu: {str(e)}")
