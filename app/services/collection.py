from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.collection import (
    CollectionInDB,
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
)
from app.db.mongodb import get_database
from app.services.movie import MovieService


class CollectionService:
    def __init__(self):
        self.db = get_database()

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
                    "movie_ids": [],
                    "created_at": now,
                    "updated_at": now,
                }
            )

            # Aynı başlıkta koleksiyon var mı kontrol et
            existing_collection = await self.db.collections.find_one(
                {"user_id": user_id, "name": collection.name}
            )
            if existing_collection:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This collection name already exists.",
                )

            result = await self.db.collections.insert_one(collection_data)
            created_collection = await self.db.collections.find_one(
                {"_id": result.inserted_id}
            )
            return CollectionInDB(**created_collection)
        except Exception as e:
            self._handle_exception(e)

    async def get_user_collections(
        self, user_id: str, current_user_id: Optional[str], skip: int = 0, limit: int = 10
    ) -> List[CollectionResponse]:
        match_stage = {"user_id": user_id}
        if user_id != current_user_id:
            match_stage["is_public"] = True

        pipeline = [
            {"$match": match_stage},
            {"$sort": {"updated_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "owner_info",
                }
            },
            {"$unwind": "$owner_info"},
            {
                "$lookup": {
                    "from": "movies",
                    "localField": "movie_ids",
                    "foreignField": "_id",
                    "as": "movies_full"
                }
            },
            {
                "$addFields": {
                    "id": {"$toString": "$_id"},
                    "owner_name": "$owner_info.name",
                    "movies": "$movies_full"
                }
            },
            {"$project": {"owner_info": 0, "movies_full": 0}}
        ]
        
        collections_cursor = self.db.collections.aggregate(pipeline)
        collections = await collections_cursor.to_list(length=limit)
        return [CollectionResponse(**c) for c in collections]

    async def get_collection_by_id(
        self, collection_id: str, current_user_id: Optional[str]
    ) -> CollectionResponse:
        if not ObjectId.is_valid(collection_id):
            raise HTTPException(status_code=400, detail="Invalid collection ID")

        pipeline = [
            {"$match": {"_id": ObjectId(collection_id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "owner_info",
                }
            },
            {"$unwind": "$owner_info"},
            {
                "$lookup": {
                    "from": "movies",
                    "localField": "movie_ids",
                    "foreignField": "_id",
                    "as": "movies_full"
                }
            },
            {
                "$addFields": {
                    "id": {"$toString": "$_id"},
                    "owner_name": "$owner_info.name",
                    "movies": "$movies_full"
                }
            },
             {"$project": {"owner_info": 0, "movies_full": 0}}
        ]

        collections_cursor = self.db.collections.aggregate(pipeline)
        collections = await collections_cursor.to_list(length=1)

        if not collections:
            raise HTTPException(status_code=404, detail="Collection not found")

        collection_data = collections[0]
        
        if not collection_data.get('is_public') and collection_data.get('user_id') != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this collection")

        return CollectionResponse(**collection_data)

    async def update_collection(
        self, collection_id: str, collection_update: CollectionUpdate, user_id: str
    ) -> Optional[CollectionInDB]:
        """Koleksiyonu günceller"""
        try:
            collection_object_id = self._convert_to_object_id(collection_id)
            user_object_id = self._convert_to_object_id(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            existing_collection = await self.get_collection_by_id(str(collection_object_id), None)
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

            update_data = collection_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            # Başlık değişiyorsa, yeni başlığın benzersiz olduğunu kontrol et
            if "name" in update_data:
                existing_name = await self.db.collections.find_one(
                    {
                        "user_id": str(user_object_id),
                        "name": update_data["name"],
                        "_id": {"$ne": collection_object_id},
                    }
                )
                if existing_name:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This collection name already exists.",
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
        except Exception as e:
            self._handle_exception(e)

    async def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """Koleksiyonu siler"""
        try:
            collection_object_id = self._convert_to_object_id(collection_id)
            user_object_id = self._convert_to_object_id(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection_by_id(str(collection_object_id), None)
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
        except Exception as e:
            self._handle_exception(e)

    async def add_movie_to_collection(
        self, collection_id: str, movie_id: str, user_id: str
    ) -> bool:
        """Koleksiyona içerik ekler"""
        try:
            collection_object_id = self._convert_to_object_id(collection_id)
            content_object_id = self._convert_to_object_id(movie_id)
            user_object_id = self._convert_to_object_id(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection_by_id(str(collection_object_id), None)
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
            movie = await self.db.movies.find_one({"_id": content_object_id})
            if not movie:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="İçerik bulunamadı"
                )

            # İçeriği koleksiyona ekle
            if str(content_object_id) not in collection.movie_ids:
                result = await self.db.collections.update_one(
                    {"_id": collection_object_id},
                    {
                        "$addToSet": {"movie_ids": str(content_object_id)},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )
                return result.modified_count > 0
            return False
        except Exception as e:
            self._handle_exception(e)

    async def remove_movie_from_collection(
        self, collection_id: str, movie_id: str, user_id: str
    ) -> bool:
        """Koleksiyondan içerik çıkarır"""
        try:
            collection_object_id = self._convert_to_object_id(collection_id)
            content_object_id = self._convert_to_object_id(movie_id)
            user_object_id = self._convert_to_object_id(user_id)

            # Koleksiyonun var olduğunu ve kullanıcıya ait olduğunu kontrol et
            collection = await self.get_collection_by_id(str(collection_object_id), None)
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
            if str(content_object_id) in collection.movie_ids:
                result = await self.db.collections.update_one(
                    {"_id": collection_object_id},
                    {
                        "$pull": {"movie_ids": str(content_object_id)},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )
                return result.modified_count > 0
            return False
        except Exception as e:
            self._handle_exception(e)

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
        except Exception as e:
            self._handle_exception(e)
