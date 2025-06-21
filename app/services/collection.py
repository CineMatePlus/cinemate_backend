from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId

from app.models.collection import (
    CollectionInDB,
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
)
from app.db.mongodb import get_database
from app.models.movie import MovieResponse
from app.services.movie import MovieService
from app.models.pyobjectid import PyObjectId


class CollectionService:
    def __init__(self):
        self.db = get_database()

    async def create_collection(
        self, collection_data: CollectionCreate, user_id: str
    ) -> CollectionInDB:
        """Yeni bir koleksiyon oluşturur"""
        user_object_id = ObjectId(user_id)
        
        existing_collection = await self.db.collections.find_one(
            {"user_id": user_object_id, "name": collection_data.name}
        )
        if existing_collection:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This collection name already exists.",
            )

        now = datetime.utcnow()
        db_collection = collection_data.dict()
        db_collection.update(
            {
                "user_id": user_object_id,
                "movie_ids": [],
                "created_at": now,
                "updated_at": now,
            }
        )

        result = await self.db.collections.insert_one(db_collection)
        
        created_collection = await self.db.collections.find_one(
            {"_id": result.inserted_id}
        )
        
        if created_collection:
            return CollectionInDB(**created_collection)
        
        raise HTTPException(status_code=500, detail="Collection could not be created.")

    async def get_user_collections(
        self, user_id: str, current_user_id: Optional[str], skip: int = 0, limit: int = 10
    ) -> List[CollectionResponse]:
        user_object_id = ObjectId(user_id)
        match_stage = {"user_id": user_object_id}
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
                "$addFields": {
                    "owner_name": "$owner_info.name",
                    "movie_count": {"$size": "$movie_ids"}
                }
            },
            {"$project": {"owner_info": 0}}
        ]
        
        collections_cursor = self.db.collections.aggregate(pipeline)
        collections = await collections_cursor.to_list(length=limit)
        return [CollectionResponse(**c) for c in collections]

    async def get_collection_by_id(
        self, collection_id: str, current_user_id: Optional[str]
    ) -> CollectionResponse:
        collection_object_id = ObjectId(collection_id)

        pipeline = [
            {"$match": {"_id": collection_object_id}},
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
                "$addFields": {
                    "owner_name": "$owner_info.name",
                    "movie_count": {"$size": "$movie_ids"}
                }
            },
             {"$project": {"owner_info": 0}}
        ]

        collections_cursor = self.db.collections.aggregate(pipeline)
        collections = await collections_cursor.to_list(length=1)

        if not collections:
            raise HTTPException(status_code=404, detail="Collection not found")

        collection_data = collections[0]
        
        if not collection_data.get('is_public') and str(collection_data.get('user_id')) != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this collection")

        return CollectionResponse(**collection_data)
    
    async def _get_collection_and_validate_owner(self, collection_id: str, user_id: str) -> dict:
        collection_obj_id = ObjectId(collection_id)
        user_obj_id = ObjectId(user_id)

        collection = await self.db.collections.find_one({"_id": collection_obj_id})

        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        if collection["user_id"] != user_obj_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this collection")
        
        return collection

    async def update_collection(
        self, collection_id: str, collection_update: CollectionUpdate, user_id: str
    ) -> CollectionResponse:
        """Koleksiyonu günceller"""
        await self._get_collection_and_validate_owner(collection_id, user_id)
        
        update_data = collection_update.dict(exclude_unset=True)
        if not update_data:
             raise HTTPException(status_code=400, detail="No update data provided")

        update_data["updated_at"] = datetime.utcnow()

        if "name" in update_data:
            existing_name = await self.db.collections.find_one(
                {
                    "user_id": ObjectId(user_id),
                    "name": update_data["name"],
                    "_id": {"$ne": ObjectId(collection_id)},
                }
            )
            if existing_name:
                raise HTTPException(status_code=409, detail="This collection name already exists.")

        await self.db.collections.update_one(
            {"_id": ObjectId(collection_id)}, {"$set": update_data}
        )

        return await self.get_collection_by_id(collection_id, user_id)

    async def delete_collection(self, collection_id: str, user_id: str) -> bool:
        await self._get_collection_and_validate_owner(collection_id, user_id)
        
        result = await self.db.collections.delete_one({"_id": ObjectId(collection_id)})
        
        if result.deleted_count == 1:
            return True
        return False

    async def add_movie_to_collection(
        self, collection_id: str, movie_id: str, user_id: str
    ) -> bool:
        await self._get_collection_and_validate_owner(collection_id, user_id)
        
        movie_obj_id = ObjectId(movie_id)
        movie = await self.db.movies.find_one({"_id": movie_obj_id})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        result = await self.db.collections.update_one(
            {"_id": ObjectId(collection_id)},
            {"$addToSet": {"movie_ids": movie_obj_id}}
        )

        return result.modified_count > 0

    async def remove_movie_from_collection(
        self, collection_id: str, movie_id: str, user_id: str
    ) -> bool:
        await self._get_collection_and_validate_owner(collection_id, user_id)

        result = await self.db.collections.update_one(
            {"_id": ObjectId(collection_id)},
            {"$pull": {"movie_ids": ObjectId(movie_id)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found in this collection")

        return result.modified_count > 0

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

    async def get_movies_in_collection(self, collection_id: str, current_user_id: Optional[str], skip: int, limit: int) -> List[MovieResponse]:
        collection = await self.db.collections.find_one({"_id": ObjectId(collection_id)})
        
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        if not collection.get('is_public') and str(collection.get('user_id')) != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this collection")

        movie_ids = collection.get("movie_ids", [])
        
        paginated_movie_ids = movie_ids[skip : skip + limit]

        if not paginated_movie_ids:
            return []

        movies_pipeline = [
            {"$match": {"_id": {"$in": paginated_movie_ids}}},
            # Gerekirse sıralama ekleyebiliriz, örn: {"$addFields": {"__order": {"$indexOfArray": [paginated_movie_ids, "$_id"]}}}, {"$sort": {"__order": 1}}
        ]
        
        # Film listesini kullanıcı etkileşimleriyle zenginleştirelim
        if current_user_id:
            movies_pipeline.extend(MovieService._get_user_interaction_pipeline(current_user_id))
        
        movies_pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})
        
        movies_cursor = self.db.movies.aggregate(movies_pipeline)
        movies = await movies_cursor.to_list(length=limit)
        
        # Orijinal sıralamayı korumak için
        movies_dict = {movie['_id']: movie for movie in movies}
        sorted_movies = [MovieResponse(**movies_dict[str(oid)]) for oid in paginated_movie_ids if str(oid) in movies_dict]

        return sorted_movies
