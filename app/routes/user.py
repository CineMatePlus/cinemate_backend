from fastapi import APIRouter, Depends, Query
from typing import List, Literal
from app.services.interaction import InteractionService
from app.services.movie import MovieService
from app.services.user import UserService
from app.models.user import UserInDB, UserResponse, SimilarUserResponse
from app.models.movie import MovieResponse
from app.routes.collection import get_current_user_required

router = APIRouter(
    tags=["Users"]
)

interaction_service = InteractionService()
user_service = UserService()

@router.get("/me/liked-movies", response_model=List[MovieResponse])
async def get_my_liked_movies(
    current_user: UserInDB = Depends(get_current_user_required),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Returns a list of movies liked by the current user."""
    return await interaction_service.get_liked_movies(current_user.id, skip, limit)

@router.get("/me/watchlist", response_model=List[MovieResponse])
async def get_my_watchlist(
    current_user: UserInDB = Depends(get_current_user_required),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Returns the current user's watchlist."""
    return await interaction_service.get_watchlist(current_user.id, skip, limit)

@router.get("/me/watched-history", response_model=List[MovieResponse])
async def get_my_watched_history(
    current_user: UserInDB = Depends(get_current_user_required),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Returns the current user's watched history."""
    return await interaction_service.get_watched_history(current_user.id, skip, limit)

@router.get("/me/similar-users", response_model=List[SimilarUserResponse])
async def get_my_similar_users(
    current_user: UserInDB = Depends(get_current_user_required),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Returns a list of users with similar tastes to the current user.
    """
    return await user_service.get_similar_users(user_id=str(current_user.id), limit=limit)

@router.get("/me/recommendations", response_model=List[MovieResponse])
async def get_my_recommendations(
    current_user: UserInDB = Depends(get_current_user_required),
    based_on: Literal["like", "watched", "watchlist"] = Query("like"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Returns movie recommendations for the current user based on a specified list.
    """
    # 1. Get the list of movie IDs from the specified user list (e.g., liked movies)
    movie_ids = await interaction_service.get_movie_ids_by_interaction(
        user_id=current_user.id,
        interaction_type=based_on
    )

    if not movie_ids:
        # If the user has no movies in the list, we can't generate recommendations.
        # We could return a generic popular list here in the future.
        return []

    # 2. Get recommendations based on the collected movie IDs
    recommendations = await MovieService.get_recommendations_from_movie_ids(
        movie_ids=movie_ids,
        user_id=current_user.id,
        limit=limit
    )

    return recommendations

@router.get("/me/stats")
async def get_my_stats(
    current_user: UserInDB = Depends(get_current_user_required)
):
    """
    Returns the number of items in the current user's liked, watched, and watchlist.
    """
    return await interaction_service.get_user_interaction_counts(current_user.id) 