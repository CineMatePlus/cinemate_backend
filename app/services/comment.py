from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.comment import (
    CommentCreate,
    CommentUpdate,
    CommentInDB,
    CommentResponse,
)
from app.db.mongodb import get_database


class CommentService:
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

    async def create_comment(
        self, content_id: str, comment: CommentCreate, user_id: str
    ) -> CommentResponse:
        """İçeriğe yorum ekler"""
        try:
            # İçeriğin var olduğunu kontrol et
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            # Yorum oluştur
            comment_dict = comment.dict()
            comment_dict.update(
                {
                    "content_id": str(content_object_id),
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )

            # Yorumu veritabanına ekle
            result = await self.db.comments.insert_one(comment_dict)
            comment_dict["_id"] = str(result.inserted_id)

            # İçerikteki yorum sayısını güncelle
            await self.db.contents.update_one(
                {"_id": content_object_id}, {"$inc": {"num_comments": 1}}
            )

            return CommentResponse(**comment_dict)
        except Exception as e:
            self._handle_exception(e)

    async def get_comments(
        self, content_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentResponse]:
        """İçeriğin yorumlarını getirir"""
        try:
            # İçeriğin var olduğunu kontrol et
            content_object_id = self._convert_to_object_id(content_id)
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            # Yorumları getir
            comments = (
                await self.db.comments.find({"content_id": content_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )

            return [
                CommentResponse(**{**comment, "_id": str(comment["_id"])})
                for comment in comments
            ]
        except Exception as e:
            self._handle_exception(e)

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
    ) -> CommentResponse:
        """Yorumu günceller"""
        try:
            # Yorumu bul
            comment_object_id = self._convert_to_object_id(comment_id)
            comment = await self.db.comments.find_one({"_id": comment_object_id})
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Yorum bulunamadı"
                )

            # Yorumun kullanıcıya ait olduğunu kontrol et
            if comment["user_id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu yorumu güncelleme yetkiniz yok",
                )

            # Yorumu güncelle
            update_data = comment_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            await self.db.comments.update_one(
                {"_id": comment_object_id}, {"$set": update_data}
            )

            # Güncellenmiş yorumu dön
            updated_comment = await self.db.comments.find_one(
                {"_id": comment_object_id}
            )
            return CommentResponse(
                **{**updated_comment, "_id": str(updated_comment["_id"])}
            )
        except Exception as e:
            self._handle_exception(e)

    async def delete_comment(self, comment_id: str, user_id: str) -> dict:
        """Yorumu siler"""
        try:
            # Yorumu bul
            comment_object_id = self._convert_to_object_id(comment_id)
            comment = await self.db.comments.find_one({"_id": comment_object_id})
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Yorum bulunamadı"
                )

            # Yorumun kullanıcıya ait olduğunu kontrol et
            if comment["user_id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu yorumu silme yetkiniz yok",
                )

            # Yorumu sil
            await self.db.comments.delete_one({"_id": comment_object_id})

            # İçerikteki yorum sayısını güncelle
            await self.db.contents.update_one(
                {"_id": ObjectId(comment["content_id"])}, {"$inc": {"num_comments": -1}}
            )

            return {"message": "Yorum başarıyla silindi"}
        except Exception as e:
            self._handle_exception(e)

    async def get_user_comments(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentResponse]:
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
                CommentResponse(**{**comment, "_id": str(comment["_id"])})
                for comment in comments
            ]
        except Exception as e:
            self._handle_exception(e)
