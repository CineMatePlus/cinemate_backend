from fastapi import APIRouter, Depends, Query
from typing import List
from app.services.interaction import InteractionService
from app.models.user import UserInDB
from app.models.movie import MovieResponse
from app.routes.collection import get_current_user_required

router = APIRouter(
    tags=["Users"]
)

interaction_service = InteractionService()

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