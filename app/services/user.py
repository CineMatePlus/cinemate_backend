from datetime import datetime
from typing import List, Optional
from bson import ObjectId
import numpy as np

from app.db.mongodb import get_database
from app.models.user import UserResponse

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
            {"user_id": user_object_id, "interaction_type": "like"},
            {"movie_id": 1}
        )
        liked_movie_ids = [item["movie_id"] for item in await liked_interactions_cursor.to_list(length=None)]

        if not liked_movie_ids:
            # If user has no liked movies, remove the embedding
            await self.db.users.update_one({"_id": user_object_id}, {"$unset": {"embedding": ""}})
            return

        # 2. Fetch embeddings of the liked movies
        movies_cursor = self.db.movies.find(
            {"_id": {"$in": liked_movie_ids}, "embedding": {"$exists": True}},
            {"embedding": 1}
        )
        movie_embeddings = [movie["embedding"] for movie in await movies_cursor.to_list(length=None)]

        if not movie_embeddings:
            # No liked movies have embeddings, so nothing to calculate
            await self.db.users.update_one({"_id": user_object_id}, {"$unset": {"embedding": ""}})
            return

        # 3. Calculate the average embedding
        average_embedding = np.mean(movie_embeddings, axis=0).tolist()

        # 4. Update the user's document with the new embedding
        await self.db.users.update_one(
            {"_id": user_object_id},
            {"$set": {"embedding": average_embedding, "updated_at": datetime.utcnow()}}
        )

    async def get_similar_users(self, user_id: str, limit: int = 10) -> List[UserResponse]:
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
        
        # 2. Use $vectorSearch to find similar users
        # Note: A vector search index on the 'embedding' field of the 'users' collection is required.
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "user_vector_index", # You'll need to create this index in Atlas
                    "path": "embedding",
                    "queryVector": user_embedding,
                    "numCandidates": 150,
                    "limit": limit + 1 # +1 to include the user itself, which we'll filter out
                }
            },
            {
                "$addFields": {
                    "similarity_score": { "$meta": "vectorSearchScore" }
                }
            },
            {
                "$match": {
                    "_id": {"$ne": user_object_id} # Exclude the user from their own similar list
                }
            },
            {"$limit": limit},
            {"$addFields": {"_id": {"$toString": "$_id"}}}
        ]

        similar_users_cursor = self.db.users.aggregate(pipeline)
        similar_users = await similar_users_cursor.to_list(length=limit)

        print("\n--- Similar Users Found ---")
        for user in similar_users:
            score = user.get('similarity_score', 'N/A')
            print(f"User: {user.get('name', 'Unknown')}, Similarity Score: {score:.4f}")
        print("---------------------------\n")

        return [UserResponse(**u) for u in similar_users] 