from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.models.collection import CollectionCreate, CollectionInDB, CollectionUpdate


async def create_collection(
    db: AsyncDatabase, collection: CollectionCreate, user_id: str
) -> CollectionInDB:
    """Yeni bir koleksiyon oluşturur"""
    now = datetime.now(timezone.utc)
    collection_data = collection.model_dump()
    collection_data.update(
        {"user_id": user_id, "movie_ids": [], "created_at": now, "updated_at": now}
    )

    result = await db.collections.insert_one(collection_data)
    created_collection = await db.collections.find_one({"_id": result.inserted_id})
    return CollectionInDB(**created_collection)


async def get_collections(
    db: AsyncDatabase, user_id: str, skip: int = 0, limit: int = 10
) -> List[CollectionInDB]:
    """Kullanıcının koleksiyonlarını getirir"""
    cursor = db.collections.find({"user_id": user_id}).skip(skip).limit(limit)
    collections = await cursor.to_list(length=limit)
    return [CollectionInDB(**collection) for collection in collections]


async def get_collection(
    db: AsyncDatabase, collection_id: str
) -> Optional[CollectionInDB]:
    """Belirli bir koleksiyonu getirir"""
    collection = await db.collections.find_one({"_id": ObjectId(collection_id)})
    if collection:
        return CollectionInDB(**collection)
    return None


async def update_collection(
    db: AsyncDatabase, collection_id: str, collection: CollectionUpdate
) -> Optional[CollectionInDB]:
    """Koleksiyonu günceller"""
    update_data = collection.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await db.collections.update_one(
        {"_id": ObjectId(collection_id)}, {"$set": update_data}
    )

    if result.modified_count:
        updated_collection = await db.collections.find_one(
            {"_id": ObjectId(collection_id)}
        )
        return CollectionInDB(**updated_collection)
    return None


async def delete_collection(db: AsyncDatabase, collection_id: str) -> bool:
    """Koleksiyonu siler"""
    result = await db.collections.delete_one({"_id": ObjectId(collection_id)})
    return result.deleted_count > 0


async def add_movie_to_collection(
    db: AsyncDatabase, collection_id: str, movie_id: str
) -> bool:
    """Koleksiyona içerik ekler"""
    result = await db.collections.update_one(
        {"_id": ObjectId(collection_id)},
        {
            "$addToSet": {"movie_ids": movie_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    return result.modified_count > 0


async def remove_movie_from_collection(
    db: AsyncDatabase, collection_id: str, movie_id: str
) -> bool:
    """Koleksiyondan içerik kaldırır"""
    result = await db.collections.update_one(
        {"_id": ObjectId(collection_id)},
        {
            "$pull": {"movie_ids": movie_id},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    return result.modified_count > 0


async def get_public_collections(
    db: AsyncDatabase, user_id: str, skip: int = 0, limit: int = 10
) -> List[CollectionInDB]:
    """Kullanıcının public koleksiyonlarını getirir"""
    cursor = (
        db.collections.find({"user_id": user_id, "is_public": True})
        .skip(skip)
        .limit(limit)
    )
    collections = await cursor.to_list(length=limit)
    return [CollectionInDB(**collection) for collection in collections]
