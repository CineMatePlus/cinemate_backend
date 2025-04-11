from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.collection import CollectionInDB, CollectionCreate, CollectionUpdate
from app.db.mongodb import get_database


class CollectionService:
    def __init__(self):
        self.db = get_database()

    async def create_collection(
        self, collection: CollectionCreate, user_id: str
    ) -> CollectionInDB:
        """Yeni bir koleksiyon oluşturur"""
        try:
            now = datetime.utcnow()
            collection_data = collection.dict()
            collection_data.update(
                {
                    "user_id": user_id,
                    "content_ids": [],
                    "created_at": now,
                    "updated_at": now,
                }
            )

            # Aynı başlıkta koleksiyon var mı kontrol et
            existing_collection = await self.db.collections.find_one(
                {"user_id": user_id, "title": collection.title}
            )
            if existing_collection:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bu başlıkta bir koleksiyon zaten mevcut",
                )

            result = await self.db.collections.insert_one(collection_data)
            created_collection = await self.db.collections.find_one(
                {"_id": result.inserted_id}
            )
            return CollectionInDB(
                **{**created_collection, "_id": str(created_collection["_id"])}
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz veri: {str(e)}",
            )

    async def get_collections(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[CollectionInDB]:
        """Kullanıcının koleksiyonlarını getirir"""
        try:
            collections = (
                await self.db.collections.find({"user_id": user_id})
                .sort("updated_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )

            return [
                CollectionInDB(**{**collection, "_id": str(collection["_id"])})
                for collection in collections
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz kullanıcı ID formatı: {str(e)}",
            )

    async def get_collection(self, collection_id: str) -> Optional[CollectionInDB]:
        """Belirli bir koleksiyonu getirir"""
        try:
            collection_object_id = ObjectId(collection_id)
            collection = await self.db.collections.find_one(
                {"_id": collection_object_id}
            )
            if collection:
                return CollectionInDB(**{**collection, "_id": str(collection["_id"])})
            return None
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz koleksiyon ID formatı: {str(e)}",
            )

    async def update_collection(
        self, collection_id: str, collection: CollectionUpdate, user_id: str
    ) -> Optional[CollectionInDB]:
        """Koleksiyonu günceller"""
        try:
            collection_object_id = ObjectId(collection_id)
            user_object_id = ObjectId(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            existing_collection = await self.get_collection(str(collection_object_id))
            if not existing_collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Koleksiyon bulunamadı",
                )
            if existing_collection.user_id != str(user_object_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu koleksiyonu güncelleme yetkiniz yok",
                )

            update_data = collection.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            # Başlık değişiyorsa, yeni başlığın benzersiz olduğunu kontrol et
            if "title" in update_data:
                existing_title = await self.db.collections.find_one(
                    {
                        "user_id": str(user_object_id),
                        "title": update_data["title"],
                        "_id": {"$ne": collection_object_id},
                    }
                )
                if existing_title:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Bu başlıkta bir koleksiyon zaten mevcut",
                    )

            await self.db.collections.update_one(
                {"_id": collection_object_id}, {"$set": update_data}
            )

            updated_collection = await self.db.collections.find_one(
                {"_id": collection_object_id}
            )
            return CollectionInDB(
                **{**updated_collection, "_id": str(updated_collection["_id"])}
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz ID formatı: {str(e)}",
            )

    async def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """Koleksiyonu siler"""
        try:
            collection_object_id = ObjectId(collection_id)
            user_object_id = ObjectId(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection(str(collection_object_id))
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Koleksiyon bulunamadı",
                )
            if collection.user_id != str(user_object_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu koleksiyonu silme yetkiniz yok",
                )

            result = await self.db.collections.delete_one({"_id": collection_object_id})
            return result.deleted_count > 0
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz ID formatı: {str(e)}",
            )

    async def add_content_to_collection(
        self, collection_id: str, content_id: str, user_id: str
    ) -> bool:
        """Koleksiyona içerik ekler"""
        try:
            collection_object_id = ObjectId(collection_id)
            content_object_id = ObjectId(content_id)
            user_object_id = ObjectId(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection(str(collection_object_id))
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Koleksiyon bulunamadı",
                )
            if collection.user_id != str(user_object_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu koleksiyonu düzenleme yetkiniz yok",
                )

            # İçeriğin var olduğunu kontrol et
            content = await self.db.contents.find_one({"_id": content_object_id})
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            # İçeriği koleksiyona ekle
            if str(content_object_id) not in collection.content_ids:
                result = await self.db.collections.update_one(
                    {"_id": collection_object_id},
                    {
                        "$addToSet": {"content_ids": str(content_object_id)},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )
                return result.modified_count > 0
            return False
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz ID formatı: {str(e)}",
            )

    async def remove_content_from_collection(
        self, collection_id: str, content_id: str, user_id: str
    ) -> bool:
        """Koleksiyondan içerik çıkarır"""
        try:
            collection_object_id = ObjectId(collection_id)
            content_object_id = ObjectId(content_id)
            user_object_id = ObjectId(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection(str(collection_object_id))
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Koleksiyon bulunamadı",
                )
            if collection.user_id != str(user_object_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bu koleksiyonu düzenleme yetkiniz yok",
                )

            # İçeriği koleksiyondan çıkar
            if str(content_object_id) in collection.content_ids:
                result = await self.db.collections.update_one(
                    {"_id": collection_object_id},
                    {
                        "$pull": {"content_ids": str(content_object_id)},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )
                return result.modified_count > 0
            return False
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz ID formatı: {str(e)}",
            )

    async def get_public_collections(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[CollectionInDB]:
        """Kullanıcının public koleksiyonlarını getirir"""
        try:
            collections = (
                await self.db.collections.find({"user_id": user_id, "is_public": True})
                .sort("updated_at", -1)
                .skip(skip)
                .limit(limit)
                .to_list(length=limit)
            )

            return [
                CollectionInDB(**{**collection, "_id": str(collection["_id"])})
                for collection in collections
            ]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz kullanıcı ID formatı: {str(e)}",
            )
