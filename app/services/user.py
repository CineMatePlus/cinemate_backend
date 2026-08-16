from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.user import SimilarUserResponse
from app.services.vector_math import average_vectors
from app.services.vector_search import (
    build_vector_search_stage,
    record_vector_search,
    start_vector_search_timer,
)


class UserService:
    def __init__(self):
        self.db = get_database()
        # To avoid circular imports, we import services here if needed or use them directly
        # from app.services.interaction import InteractionService

    async def update_user_embedding(self, user_id: str):
        """
        Calculates and updates the user's taste embedding vector based on their liked movies.
        """
        user_object_id = ObjectId(user_id)

        # 1. Fetch all 'like' interactions for the user
        liked_interactions_cursor = self.db.interactions.find(
            {"user_id": user_object_id, "interaction_type": "like"}, {"movie_id": 1}
        )
        liked_movie_ids = [
            item["movie_id"]
            for item in await liked_interactions_cursor.to_list(length=None)
        ]

        if not liked_movie_ids:
            # If user has no liked movies, remove the embedding
            await self._clear_embedding(user_object_id)
            return

        # 2. Fetch embeddings of the liked movies
        movies_cursor = self.db.movies.find(
            {"_id": {"$in": liked_movie_ids}, "embedding": {"$exists": True}},
            {"embedding": 1},
        )
        movie_embeddings = [
            movie["embedding"] for movie in await movies_cursor.to_list(length=None)
        ]

        if not movie_embeddings:
            # No liked movies have embeddings, so nothing to calculate
            await self._clear_embedding(user_object_id)
            return

        # 3. Calculate the average embedding
        average_embedding = average_vectors(movie_embeddings)

        # 4. Update the user's document with the new embedding
        await self.db.users.update_one(
            {"_id": user_object_id},
            {
                "$set": {
                    "embedding": average_embedding,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    async def _clear_embedding(self, user_object_id: ObjectId) -> None:
        await self.db.users.update_one(
            {"_id": user_object_id},
            {"$unset": {"embedding": ""}},
        )

    async def get_similar_users(
        self, user_id: str, limit: int = 10
    ) -> List[SimilarUserResponse]:
        """
        Finds users with similar tastes based on their embedding vector.
        """
        user_object_id = ObjectId(user_id)

        # 1. Get the target user's embedding
        user = await self.db.users.find_one({"_id": user_object_id})
        if not user or "embedding" not in user:
            # Cannot find similar users if the source user has no embedding
            return []

        user_embedding = user["embedding"]

        search_limit = limit + 1
        pipeline = [
            build_vector_search_stage(
                index=settings.USER_VECTOR_INDEX,
                query_vector=user_embedding,
                limit=search_limit,
            ),
            {"$addFields": {"similarity": {"$meta": "vectorSearchScore"}}},
            {
                "$match": {
                    "_id": {
                        "$ne": user_object_id
                    }  # Exclude the user from their own similar list
                }
            },
            {"$limit": limit},
            {"$addFields": {"_id": {"$toString": "$_id"}}},
            {"$project": {"embedding": 0}},
        ]

        started_at = start_vector_search_timer()
        similar_users_cursor = self.db.users.aggregate(pipeline)
        similar_users = await similar_users_cursor.to_list(length=limit)
        record_vector_search("similar_users", started_at, similar_users, "similarity")

        return [SimilarUserResponse(**u) for u in similar_users]
