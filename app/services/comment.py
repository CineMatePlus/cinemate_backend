from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.validation import object_id
from app.db.mongodb import get_database
from app.models.comment import (
    CommentCreate,
    CommentData,
    CommentInDB,
    CommentResponse,
    CommentUpdate,
)
from app.models.user import PublicUserResponse


class CommentService:
    def __init__(self, db: AsyncDatabase | None = None):
        self.db = db if db is not None else get_database()

    async def _enrich_comments_with_user_data(
        self, comments: List[dict]
    ) -> List[CommentResponse]:
        if not comments:
            return []
        users = await self.db.users.find(
            {"_id": {"$in": [object_id(c["user_id"]) for c in comments]}},
            {"name": 1, "avatar_url": 1, "gender": 1, "created_at": 1, "updated_at": 1},
        ).to_list(length=None)
        by_id = {str(user["_id"]): {**user, "_id": str(user["_id"])} for user in users}
        now = datetime.now(timezone.utc)
        return [
            CommentResponse(
                comment=CommentData(**{**comment, "_id": str(comment["_id"])}),
                user=PublicUserResponse(
                    **by_id.get(
                        comment["user_id"],
                        {
                            "_id": comment["user_id"],
                            "name": "Silinmiş Kullanıcı",
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                ),
            )
            for comment in comments
        ]

    async def create_comment(
        self, movie_id: str, comment: CommentCreate, user_id: str
    ) -> CommentResponse:
        mid = object_id(movie_id)
        now = datetime.now(timezone.utc)
        data = {
            **comment.model_dump(),
            "movie_id": str(mid),
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
        }

        async def create(session):
            result = await self.db.movies.update_one(
                {"_id": mid}, {"$inc": {"num_comments": 1}}, session=session
            )
            if not result.matched_count:
                raise HTTPException(status_code=404, detail="İçerik bulunamadı")
            inserted = await self.db.comments.insert_one(dict(data), session=session)
            return {**data, "_id": inserted.inserted_id}

        async with self.db.client.start_session() as session:
            created = await session.with_transaction(create)
        return (await self._enrich_comments_with_user_data([created]))[0]

    async def get_comments(
        self, movie_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentResponse]:
        mid = object_id(movie_id)
        if not await self.db.movies.find_one({"_id": mid}, {"_id": 1}):
            raise HTTPException(status_code=404, detail="İçerik bulunamadı")
        comments = (
            await self.db.comments.find({"movie_id": str(mid)})
            .sort([("created_at", -1), ("_id", -1)])
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        return await self._enrich_comments_with_user_data(comments)

    async def get_comment(self, comment_id: str) -> Optional[CommentInDB]:
        cid = object_id(comment_id)
        comment = await self.db.comments.find_one({"_id": cid})
        return CommentInDB(**{**comment, "_id": str(cid)}) if comment else None

    async def _check_owner(self, cid, user_id, session=None):
        comment = await self.db.comments.find_one({"_id": cid}, session=session)
        if not comment:
            raise HTTPException(status_code=404, detail="Yorum bulunamadı")
        if comment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Bu yorum için yetkiniz yok")
        return comment

    async def update_comment(
        self, comment_id: str, comment_update: CommentUpdate, user_id: str
    ) -> CommentResponse:
        cid = object_id(comment_id)
        await self._check_owner(cid, user_id)
        comment = await self.db.comments.find_one_and_update(
            {"_id": cid, "user_id": user_id},
            {
                "$set": {
                    **comment_update.model_dump(),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Yorum bulunamadı")
        return (await self._enrich_comments_with_user_data([comment]))[0]

    async def delete_comment(self, comment_id: str, user_id: str) -> dict:
        cid = object_id(comment_id)

        async def delete(session):
            comment = await self._check_owner(cid, user_id, session=session)
            await self.db.comments.delete_one(
                {"_id": cid, "user_id": user_id}, session=session
            )
            await self.db.movies.update_one(
                {"_id": object_id(comment["movie_id"])},
                {"$inc": {"num_comments": -1}},
                session=session,
            )

        async with self.db.client.start_session() as session:
            await session.with_transaction(delete)
        return {"message": "Yorum başarıyla silindi"}

    async def get_user_comments(
        self, user_id: str, skip: int = 0, limit: int = 10
    ) -> List[CommentResponse]:
        comments = (
            await self.db.comments.find({"user_id": user_id})
            .sort([("created_at", -1), ("_id", -1)])
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        return await self._enrich_comments_with_user_data(comments)
