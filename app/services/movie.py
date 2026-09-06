from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.movie import MovieResponse
from app.services.vector_math import average_vectors
from app.services.vector_search import (
    build_vector_search_stage,
    record_vector_search,
    start_vector_search_timer,
)

db = get_database()


class MovieService:
    @staticmethod
    async def get_movies(
        user_id: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[MovieResponse]:
        pipeline = [{"$sort": {"_id": 1}}, {"$skip": skip}, {"$limit": limit}]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        movies_cursor = await db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    async def get_movies_by_genre(
        genre: str, user_id: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[MovieResponse]:
        pipeline = [
            {"$match": {"genres": genre}},
            {"$sort": {"_id": 1}},
            {"$skip": skip},
            {"$limit": limit},
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        movies_cursor = await db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    async def get_movie_by_id(
        movie_id: str, user_id: Optional[str] = None
    ) -> MovieResponse:
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        pipeline = [{"$match": {"_id": ObjectId(movie_id)}}]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        movies_cursor = await db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=1)

        if not movies:
            raise HTTPException(status_code=404, detail="Movie not found")

        return MovieResponse(**movies[0])

    @staticmethod
    async def search_movies_by_vector(
        embedding: List[float], user_id: Optional[str] = None, limit: int = 10
    ) -> List[MovieResponse]:
        pipeline = [
            build_vector_search_stage(
                index=settings.MOVIE_VECTOR_INDEX,
                query_vector=embedding,
                limit=limit,
            ),
            {"$addFields": {"similarity_score": {"$meta": "vectorSearchScore"}}},
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        started_at = start_vector_search_timer()
        movies_cursor = await db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=limit)
        record_vector_search(
            "movie_text_search", started_at, movies, "similarity_score"
        )

        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    async def get_recommendations_from_movie_ids(
        movie_ids: List[str], user_id: Optional[str] = None, limit: int = 10
    ) -> List[MovieResponse]:
        if not movie_ids:
            return []

        object_ids = [ObjectId(id) for id in movie_ids if ObjectId.is_valid(id)]

        movies_cursor = db.movies.find(
            {"_id": {"$in": object_ids}, "embedding": {"$exists": True}},
            {"embedding": 1},
        )
        embeddings = [
            movie["embedding"] for movie in await movies_cursor.to_list(length=None)
        ]

        if not embeddings:
            return []

        # Calculate the average embedding vector
        average_embedding = average_vectors(embeddings)

        # Find movies similar to the average embedding, excluding the ones already in the list
        search_limit = limit + len(object_ids)
        pipeline = [
            build_vector_search_stage(
                index=settings.MOVIE_VECTOR_INDEX,
                query_vector=average_embedding,
                limit=search_limit,
            ),
            {"$addFields": {"similarity_score": {"$meta": "vectorSearchScore"}}},
            {"$match": {"_id": {"$nin": object_ids}}},
            {"$limit": limit},
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        started_at = start_vector_search_timer()
        similar_movies_cursor = await db.movies.aggregate(pipeline)
        similar_movies = await similar_movies_cursor.to_list(length=limit)
        record_vector_search(
            "movie_list_recommendations",
            started_at,
            similar_movies,
            "similarity_score",
        )

        return [MovieResponse(**movie) for movie in similar_movies]

    @staticmethod
    async def get_similar_movies(
        movie_id: str, user_id: Optional[str] = None
    ) -> List[MovieResponse]:
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        target_movie = await db.movies.find_one(
            {"_id": ObjectId(movie_id)}, {"embedding": 1, "title": 1}
        )
        if not target_movie:
            raise HTTPException(status_code=404, detail="Target movie not found")

        embedding = target_movie.get("embedding")
        if not embedding:
            raise HTTPException(
                status_code=404, detail="Embeddings for the target movie not found."
            )

        pipeline = [
            build_vector_search_stage(
                index=settings.MOVIE_VECTOR_INDEX,
                query_vector=embedding,
                limit=11,
            ),
            {"$addFields": {"similarity_score": {"$meta": "vectorSearchScore"}}},
            {"$match": {"_id": {"$ne": ObjectId(movie_id)}}},
            {"$limit": 10},
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.extend(MovieService._movie_response_pipeline())

        started_at = start_vector_search_timer()
        movies_cursor = await db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=10)
        record_vector_search("similar_movies", started_at, movies, "similarity_score")

        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    def _get_user_interaction_pipeline(user_id: str) -> List[dict]:
        if not user_id:
            return [
                {
                    "$addFields": {
                        "is_liked": False,
                        "is_watched": False,
                        "is_in_watchlist": False,
                    }
                }
            ]

        user_object_id = ObjectId(user_id)

        return [
            {
                "$lookup": {
                    "from": "interactions",
                    "let": {"movie_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$movie_id", "$$movie_id"]},
                                        {"$eq": ["$user_id", user_object_id]},
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
                                    "in": {
                                        "$eq": [
                                            "$$interaction.interaction_type",
                                            "like",
                                        ]
                                    },
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
                                    "in": {
                                        "$eq": [
                                            "$$interaction.interaction_type",
                                            "watched",
                                        ]
                                    },
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
                                    "in": {
                                        "$eq": [
                                            "$$interaction.interaction_type",
                                            "watchlist",
                                        ]
                                    },
                                }
                            }
                        ]
                    },
                },
            },
            {"$project": {"user_interactions": 0}},
        ]

    @staticmethod
    def _movie_response_pipeline() -> List[dict]:
        """Normalize MongoDB values and keep the large vector out of API results."""
        return [
            {
                "$addFields": {
                    "_id": {"$toString": "$_id"},
                    "title": {"$toString": "$title"},
                    "original_title": {"$toString": "$original_title"},
                    "production_companies": {
                        "$map": {
                            "input": {"$ifNull": ["$production_companies", []]},
                            "as": "pc",
                            "in": {"$toString": "$$pc"},
                        }
                    },
                }
            },
            {"$project": {"embedding": 0}},
        ]
