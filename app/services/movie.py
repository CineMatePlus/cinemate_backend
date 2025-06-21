from bson import ObjectId
from typing import List, Optional
from app.db.mongodb import get_database
from app.models.movie import MovieResponse
from app.models.interaction import InteractionInDB
from fastapi import HTTPException

db = get_database()


class MovieService:
    @staticmethod
    async def get_movies(user_id: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[MovieResponse]:
        pipeline = [
            {"$skip": skip},
            {"$limit": limit}
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))
        
        # Convert _id to string for Pydantic compatibility
        pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})

        movies_cursor = db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    async def get_movie_by_id(movie_id: str, user_id: Optional[str] = None) -> MovieResponse:
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        pipeline = [
            {"$match": {"_id": ObjectId(movie_id)}}
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))
        
        # Convert _id to string for Pydantic compatibility
        pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})

        movies_cursor = db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=1)

        if not movies:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        return MovieResponse(**movies[0])

    @staticmethod
    def _get_user_interaction_pipeline(user_id: str) -> List[dict]:
        return [
            {
                "$lookup": {
                    "from": "interactions",
                    "let": {"movie_id_str": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$movie_id", "$$movie_id_str"]},
                                        {"$eq": ["$user_id", user_id]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "user_interactions",
                }
            },
            {
                "$addFields": {
                    "is_liked": {
                        "$anyElementTrue": [
                            {
                                "$map": {
                                    "input": "$user_interactions",
                                    "as": "interaction",
                                    "in": {"$eq": ["$$interaction.interaction_type", "like"]},
                                }
                            }
                        ]
                    },
                    "is_watched": {
                        "$anyElementTrue": [
                            {
                                "$map": {
                                    "input": "$user_interactions",
                                    "as": "interaction",
                                    "in": {"$eq": ["$$interaction.interaction_type", "watched"]},
                                }
                            }
                        ]
                    },
                    "is_in_watchlist": {
                        "$anyElementTrue": [
                            {
                                "$map": {
                                    "input": "$user_interactions",
                                    "as": "interaction",
                                    "in": {"$eq": ["$$interaction.interaction_type", "watchlist"]},
                                }
                            }
                        ]
                    },
                },
            },
            {"$project": {"user_interactions": 0}},
        ] 