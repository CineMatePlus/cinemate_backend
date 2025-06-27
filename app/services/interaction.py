from typing import Tuple, List
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId

from app.db.mongodb import get_database
from app.models.movie import MovieResponse
from app.services.movie import MovieService
from app.services.user import UserService


class InteractionService:
    def __init__(self):
        self.db = get_database()
        self.user_service = UserService()

    async def _validate_movie_exists(self, movie_id: str):
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")
        
        movie = await self.db.movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

    def _get_counter_field(self, interaction_type: str) -> str:
        """Returns the counter field on the movie model based on interaction."""
        if interaction_type == "like":
            return "num_likes"
        elif interaction_type == "watched":
            return "num_watches"
        elif interaction_type == "watchlist":
            return None  # Watchlist does not have a counter on the movie model
        else:
            raise HTTPException(status_code=400, detail="Invalid interaction type")

    async def toggle_interaction(
        self, user_id: str, movie_id: str, interaction_type: str
    ) -> bool:
        """
        Adds or removes a user interaction for a movie.
        Returns True if the interaction was added, False if removed.
        """
        await self._validate_movie_exists(movie_id)
        counter_field = self._get_counter_field(interaction_type)

        interaction_data = {
            "user_id": ObjectId(user_id),
            "movie_id": ObjectId(movie_id),
            "interaction_type": interaction_type,
        }

        existing_interaction = await self.db.interactions.find_one(interaction_data)

        if existing_interaction:
            # Interaction exists, so remove it
            await self.db.interactions.delete_one(interaction_data)
            if counter_field:
                await self.db.movies.update_one(
                    {"_id": ObjectId(movie_id)}, {"$inc": {counter_field: -1}}
                )
            # If a like was removed, update the user's embedding
            if interaction_type == "like":
                await self.user_service.update_user_embedding(user_id)
            return False  # Removed
        else:
            # Interaction does not exist, so add it
            interaction_data["created_at"] = datetime.utcnow()
            await self.db.interactions.insert_one(interaction_data)
            if counter_field:
                await self.db.movies.update_one(
                    {"_id": ObjectId(movie_id)}, {"$inc": {counter_field: 1}}
                )
            # If a like was added, update the user's embedding
            if interaction_type == "like":
                await self.user_service.update_user_embedding(user_id)
            return True  # Added

    async def get_movie_ids_by_interaction(
        self, user_id: str, interaction_type: str
    ) -> List[str]:
        """
        Fetches a list of movie IDs for a user based on interaction type.
        """
        interactions_cursor = self.db.interactions.find(
            {"user_id": ObjectId(user_id), "interaction_type": interaction_type},
            {"movie_id": 1}
        )
        movie_ids = await interactions_cursor.to_list(length=None)
        return [str(item["movie_id"]) for item in movie_ids]

    async def _get_movie_list_by_interaction(
        self, user_id: str, interaction_type: str, skip: int, limit: int
    ) -> List[MovieResponse]:
        """
        A generic method to fetch a user's movie list based on an interaction type.
        """
        # İlk olarak, kullanıcının ilgili etkileşimlerini sayfalayarak bulalım.
        base_pipeline = [
            {"$match": {"user_id": ObjectId(user_id), "interaction_type": interaction_type}},
            {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

        # Bu etkileşimlere karşılık gelen film detaylarını çekelim.
        base_pipeline.extend([
                {
                    "$lookup": {
                    "from": "movies",
                    "localField": "movie_id",
                    "foreignField": "_id",  # Burası _id olmalı
                    "as": "movie_details"
                }
            },
            {"$unwind": "$movie_details"},
            {"$replaceRoot": {"newRoot": "$movie_details"}},
        ])

        # Artık elimizde sadece istenen sayfadaki filmler var.
        # Şimdi bu filmleri MovieService'in kanıtlanmış metoduyla zenginleştirelim.
        enrichment_pipeline = MovieService._get_user_interaction_pipeline(user_id)
        
        # ID'yi string'e çevirme adımını da ekleyelim.
        final_pipeline = base_pipeline + enrichment_pipeline + [
            {"$addFields": {"_id": {"$toString": "$_id"}}}
        ]
        
        movies_cursor = self.db.interactions.aggregate(final_pipeline)
        movies = await movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in movies]

    async def get_liked_movies(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "like", skip, limit)

    async def get_watched_history(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "watched", skip, limit)

    async def get_watchlist(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "watchlist", skip, limit)

    async def get_user_interaction_counts(self, user_id: str) -> dict:
        """
        Kullanıcının etkileşim sayılarını döndürür.
        """
        user_object_id = ObjectId(user_id)
        
        likes_count = await self.db.interactions.count_documents(
            {"user_id": user_object_id, "interaction_type": "like"}
        )
        watched_count = await self.db.interactions.count_documents(
            {"user_id": user_object_id, "interaction_type": "watched"}
        )
        watchlist_count = await self.db.interactions.count_documents(
            {"user_id": user_object_id, "interaction_type": "watchlist"}
        )
        
        return {
            "likes": likes_count,
            "watched": watched_count,
            "watchlist": watchlist_count,
        }
