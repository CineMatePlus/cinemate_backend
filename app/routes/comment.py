from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.comment import (
    CommentResponse,
    CommentCreate,
    CommentUpdate,
)
from app.db.mongodb import get_database
from app.services.comment import CommentService
from app.services.auth import AuthService
from app.models.user import UserInDB
from app.models.content import ContentInDB
from datetime import datetime
from pydantic import ValidationError

router = APIRouter(prefix="/comments", tags=["comments"])

# Servis örneği
comment_service = CommentService()
auth_service = AuthService()
get_current_active_user = auth_service.get_current_active_user


@router.post("/{content_id}", response_model=CommentResponse)
async def create_comment(
    content_id: str,
    comment: CommentCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """İçeriğe yorum ekler"""
    try:
        # İçeriğin var olduğunu kontrol et
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        # Yorum oluştur
        comment_dict = comment.dict()
        comment_dict.update(
            {
                "content_id": str(object_id),
                "user_id": str(current_user.id),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        # Yorumu veritabanına ekle
        result = await db.comments.insert_one(comment_dict)
        comment_dict["_id"] = str(result.inserted_id)

        # İçerikteki yorum sayısını güncelle
        await db.contents.update_one({"_id": object_id}, {"$inc": {"num_comments": 1}})

        return CommentResponse(**comment_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/{content_id}", response_model=List[CommentResponse])
async def get_comments(
    content_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """İçeriğin yorumlarını getirir"""
    try:
        # İçeriğin var olduğunu kontrol et
        object_id = ObjectId(content_id)
        content = await db.contents.find_one({"_id": object_id})
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        # Yorumları getir
        comments = (
            await db.comments.find({"content_id": content_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

        return [
            CommentResponse(**{**comment, "_id": str(comment["_id"])})
            for comment in comments
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content ID format: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Yorumu günceller"""
    try:
        # Yorumu bul
        object_id = ObjectId(comment_id)
        comment = await db.comments.find_one({"_id": object_id})
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        # Yorumun kullanıcıya ait olduğunu kontrol et
        if comment["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this comment",
            )

        # Yorumu güncelle
        update_data = comment_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await db.comments.update_one({"_id": object_id}, {"$set": update_data})

        # Güncellenmiş yorumu dön
        updated_comment = await db.comments.find_one({"_id": object_id})
        return CommentResponse(
            **{**updated_comment, "_id": str(updated_comment["_id"])}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid comment ID format: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Yorumu siler"""
    try:
        # Yorumu bul
        object_id = ObjectId(comment_id)
        comment = await db.comments.find_one({"_id": object_id})
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        # Yorumun kullanıcıya ait olduğunu kontrol et
        if comment["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment",
            )

        # Yorumu sil
        await db.comments.delete_one({"_id": object_id})

        # İçerikteki yorum sayısını güncelle
        await db.contents.update_one(
            {"_id": ObjectId(comment["content_id"])}, {"$inc": {"num_comments": -1}}
        )

        return {"message": "Comment deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid comment ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/user/me", response_model=List[CommentResponse])
async def get_user_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Kullanıcının kendi yorumlarını getirir"""
    try:
        # Yorumları getir
        comments = (
            await db.comments.find({"user_id": str(current_user.id)})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

        return [
            CommentResponse(**{**comment, "_id": str(comment["_id"])})
            for comment in comments
        ]
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
