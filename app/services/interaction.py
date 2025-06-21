from typing import Tuple, List
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId

from app.db.mongodb import get_database
from app.models.movie import MovieResponse


class InteractionService:
    def __init__(self):
        self.db = get_database()

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
            "user_id": user_id,
            "movie_id": movie_id,
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
            return False  # Removed
        else:
            # Interaction does not exist, so add it
            interaction_data["created_at"] = datetime.utcnow()
            await self.db.interactions.insert_one(interaction_data)
            if counter_field:
                await self.db.movies.update_one(
                    {"_id": ObjectId(movie_id)}, {"$inc": {counter_field: 1}}
                )
            return True  # Added

    async def _get_movie_list_by_interaction(
        self, user_id: str, interaction_type: str, skip: int, limit: int
    ) -> List[MovieResponse]:
        """
        A generic method to fetch a user's movie list based on an interaction type.
        """
        pipeline = [
            {"$match": {"user_id": user_id, "interaction_type": interaction_type}},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$addFields": {
                    "movie_id_obj": {"$toObjectId": "$movie_id"}
                }
            },
            {
                "$lookup": {
                    "from": "movies",
                    "localField": "movie_id_obj",
                    "foreignField": "_id",
                    "as": "movie_details"
                }
            },
            {"$unwind": "$movie_details"},
            {"$replaceRoot": {"newRoot": "$movie_details"}},
            {"$addFields": {"_id": {"$toString": "$_id"}}}
        ]
        
        movies_cursor = self.db.interactions.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in movies]

    async def get_liked_movies(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "like", skip, limit)

    async def get_watched_history(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "watched", skip, limit)

    async def get_watchlist(self, user_id: str, skip: int, limit: int) -> List[MovieResponse]:
        return await self._get_movie_list_by_interaction(user_id, "watchlist", skip, limit)
