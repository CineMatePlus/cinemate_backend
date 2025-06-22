from bson import ObjectId
from typing import List, Optional
from app.db.mongodb import get_database
from app.models.movie import MovieResponse, MovieInDB
from app.models.interaction import InteractionInDB
from fastapi import HTTPException
from app.services.ai import AIService
import numpy as np

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
    async def search_movies_by_vector(embedding: List[float], user_id: Optional[str] = None) -> List[MovieResponse]:
        # Note: A vector search index named 'vector_index' must be created on the 'movies' collection in MongoDB Atlas.
        # The index should be on the 'embedding' field.
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": 150,
                    "limit": 10
                }
            }
        ]
        
        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})
        
        movies_cursor = db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=10)
        return [MovieResponse(**movie) for movie in movies]

    @staticmethod
    async def get_recommendations_from_movie_ids(movie_ids: List[str], user_id: Optional[str] = None, limit: int = 10) -> List[MovieResponse]:
        if not movie_ids:
            return []

        object_ids = [ObjectId(id) for id in movie_ids if ObjectId.is_valid(id)]
        
        movies_cursor = db.movies.find(
            {"_id": {"$in": object_ids}, "embedding": {"$exists": True}},
            {"embedding": 1}
        )
        embeddings = [movie["embedding"] for movie in await movies_cursor.to_list(length=None)]

        if not embeddings:
            return []

        # Calculate the average embedding vector
        average_embedding = np.mean(embeddings, axis=0).tolist()

        # Find movies similar to the average embedding, excluding the ones already in the list
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": average_embedding,
                    "numCandidates": 150,
                    "limit": limit + len(object_ids) 
                }
            },
            {
                "$match": {
                    "_id": {"$nin": object_ids}
                }
            },
            {"$limit": limit}
        ]

        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})
        
        similar_movies_cursor = db.movies.aggregate(pipeline)
        similar_movies = await similar_movies_cursor.to_list(length=limit)
        return [MovieResponse(**movie) for movie in similar_movies]

    @staticmethod
    async def get_similar_movies(movie_id: str, user_id: Optional[str] = None) -> List[MovieResponse]:
        if not ObjectId.is_valid(movie_id):
            raise HTTPException(status_code=400, detail="Invalid movie ID format")

        target_movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not target_movie:
            raise HTTPException(status_code=404, detail="Target movie not found")

        target_movie_model = MovieInDB(**target_movie)

        embedding = target_movie_model.embedding
        if not embedding:
            raise HTTPException(status_code=404, detail="Embeddings for the target movie not found.")

        # Note: A vector search index named 'vector_index' must be created on the 'movies' collection in MongoDB Atlas.
        # The index should be on the 'embedding' field.
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": 150,
                    "limit": 11 # 10 similar + the movie itself
                }
            },
            {
                "$match": {
                    "_id": {"$ne": ObjectId(movie_id)}
                }
            },
            {"$limit": 10}
        ]
        
        if user_id:
            pipeline.extend(MovieService._get_user_interaction_pipeline(user_id))

        pipeline.append({"$addFields": {"_id": {"$toString": "$_id"}}})
        
        movies_cursor = db.movies.aggregate(pipeline)
        movies = await movies_cursor.to_list(length=10)
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