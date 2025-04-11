from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user_content import (
    UserContentInDB,
    UserContentResponse,
    UserContentCreate,
    UserContentUpdate,
)
from app.db.mongodb import get_database
from app.services.user_content import UserContentService
from app.services.auth import AuthService
from app.models.user import UserInDB
from app.models.content import ContentInDB
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/user-content", tags=["user-contents"])

# Servis örneği
user_content_service = UserContentService()
auth_service = AuthService()
get_current_active_user = auth_service.get_current_active_user


async def get_or_create_user_content(
    db: AsyncIOMotorDatabase, user_id: str, content_id: str
) -> UserContentInDB:
    """Kullanıcı-İçerik ilişkisini getirir veya oluşturur"""
    try:
        object_id = ObjectId(content_id)
        user_content = await db.user_contents.find_one(
            {"user_id": user_id, "content_id": str(object_id)}
        )

        if not user_content:
            user_content = {
                "user_id": user_id,
                "content_id": str(object_id),
                "is_liked": False,
                "is_watched": False,
                "in_watchlist": False,
                "rated": None,
                "last_interacted_at": datetime.utcnow(),
            }
            result = await db.user_contents.insert_one(user_content)
            user_content["_id"] = str(result.inserted_id)
            return UserContentInDB(**user_content)

        user_content["_id"] = str(user_content["_id"])
        return UserContentInDB(**user_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting or creating user content: {str(e)}",
        )


@router.post("/{content_id}/like", response_model=UserContentResponse)
async def like_content(
    content_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """İçeriği beğenir veya beğenmeyi kaldırır"""
    try:
        # İçeriğin var olduğunu kontrol et
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        # Kullanıcı-İçerik ilişkisini getir
        user_content = await get_or_create_user_content(
            db, str(current_user.id), str(object_id)
        )

        # Beğeni durumunu tersine çevir
        new_like_status = not user_content.is_liked

        # İlişkiyi güncelle
        await db.user_contents.update_one(
            {"_id": ObjectId(user_content.id)},
            {
                "$set": {
                    "is_liked": new_like_status,
                    "last_interacted_at": datetime.utcnow(),
                }
            },
        )

        # İçerikteki beğeni sayısını güncelle
        await db.contents.update_one(
            {"_id": object_id}, {"$inc": {"num_likes": 1 if new_like_status else -1}}
        )

        # Güncellenmiş ilişkiyi dön
        updated_user_content = await db.user_contents.find_one(
            {"_id": ObjectId(user_content.id)}
        )
        if not updated_user_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user content",
            )

        updated_user_content["_id"] = str(updated_user_content["_id"])
        return UserContentResponse(**updated_user_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/{content_id}/watch", response_model=UserContentResponse)
async def mark_as_watched(
    content_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """İçeriği izlendi olarak işaretler veya işareti kaldırır"""
    try:
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        user_content = await get_or_create_user_content(
            db, str(current_user.id), str(object_id)
        )

        # İzlenme durumunu tersine çevir
        new_watched_status = not user_content.is_watched

        # İlişkiyi güncelle
        await db.user_contents.update_one(
            {"_id": ObjectId(user_content.id)},
            {
                "$set": {
                    "is_watched": new_watched_status,
                    "last_interacted_at": datetime.utcnow(),
                }
            },
        )

        # İçerikteki izlenme sayısını güncelle
        await db.contents.update_one(
            {"_id": object_id},
            {"$inc": {"num_watches": 1 if new_watched_status else -1}},
        )

        updated_user_content = await db.user_contents.find_one(
            {"_id": ObjectId(user_content.id)}
        )
        if not updated_user_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user content",
            )

        updated_user_content["_id"] = str(updated_user_content["_id"])
        return UserContentResponse(**updated_user_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/{content_id}/watchlist", response_model=UserContentResponse)
async def toggle_watchlist(
    content_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """İçeriği izleme listesine ekler veya çıkarır"""
    try:
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        user_content = await get_or_create_user_content(
            db, str(current_user.id), str(object_id)
        )
        new_watchlist_status = not user_content.in_watchlist

        await db.user_contents.update_one(
            {"_id": ObjectId(user_content.id)},
            {
                "$set": {
                    "in_watchlist": new_watchlist_status,
                    "last_interacted_at": datetime.utcnow(),
                }
            },
        )

        updated_user_content = await db.user_contents.find_one(
            {"_id": ObjectId(user_content.id)}
        )
        if not updated_user_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user content",
            )

        updated_user_content["_id"] = str(updated_user_content["_id"])
        return UserContentResponse(**updated_user_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post("/{content_id}/rate", response_model=UserContentResponse)
async def rate_content(
    content_id: str,
    rating: int = Query(..., ge=1, le=10),  # 1-10 arası integer
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """İçeriği puanlar"""
    try:
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        user_content = await get_or_create_user_content(
            db, str(current_user.id), str(object_id)
        )

        # Eski puanı al
        old_rating = user_content.rated or 0

        # İlişkiyi güncelle
        await db.user_contents.update_one(
            {"_id": ObjectId(user_content.id)},
            {"$set": {"rated": rating, "last_interacted_at": datetime.utcnow()}},
        )

        # İçeriğin ortalama puanını güncelle
        content["_id"] = str(content["_id"])
        content = ContentInDB(**content)
        total_ratings = content.num_ratings
        current_avg = (
            content.average_rating or 0.0
        )  # Eğer average_rating None ise 0.0 kullan

        if old_rating == 0:  # İlk puanlama
            if total_ratings == 0:
                new_avg = float(rating)
            else:
                new_avg = (current_avg * total_ratings + float(rating)) / (
                    total_ratings + 1
                )
            await db.contents.update_one(
                {"_id": object_id},
                {"$set": {"average_rating": new_avg}, "$inc": {"num_ratings": 1}},
            )
        else:  # Puan güncelleme
            if total_ratings == 0:
                new_avg = float(rating)
            else:
                new_avg = (
                    current_avg * total_ratings - float(old_rating) + float(rating)
                ) / total_ratings
            await db.contents.update_one(
                {"_id": object_id}, {"$set": {"average_rating": new_avg}}
            )

        updated_user_content = await db.user_contents.find_one(
            {"_id": ObjectId(user_content.id)}
        )
        if not updated_user_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user content",
            )

        updated_user_content["_id"] = str(updated_user_content["_id"])
        return UserContentResponse(**updated_user_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/history", response_model=list[UserContentResponse])
async def get_watch_history(
    skip: int = 0,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Kullanıcının izleme geçmişini getirir"""
    try:
        user_contents = (
            await db.user_contents.find(
                {"user_id": str(current_user.id), "is_watched": True}
            )
            .sort("last_interacted_at", -1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

        return [
            UserContentResponse(**{**uc, "_id": str(uc["_id"])}) for uc in user_contents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/watchlist", response_model=list[UserContentResponse])
async def get_watchlist(
    skip: int = 0,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Kullanıcının izleme listesini getirir"""
    try:
        user_contents = (
            await db.user_contents.find(
                {"user_id": str(current_user.id), "in_watchlist": True}
            )
            .sort("last_interacted_at", -1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

        return [
            UserContentResponse(**{**uc, "_id": str(uc["_id"])}) for uc in user_contents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/liked", response_model=list[UserContentResponse])
async def get_liked_contents(
    skip: int = 0,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Kullanıcının beğendiği içerikleri getirir"""
    try:
        user_contents = (
            await db.user_contents.find(
                {"user_id": str(current_user.id), "is_liked": True}
            )
            .sort("last_interacted_at", -1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

        return [
            UserContentResponse(**{**uc, "_id": str(uc["_id"])}) for uc in user_contents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
