from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from app.models.movie import MovieResponse
from app.models.user import UserInDB
from app.services.movie import MovieService
from app.services.auth import AuthService
from app.services.ai import AIService
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter(tags=["movies"])
auth_service = AuthService()

async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[UserInDB]:
    if authorization is None:
        return None
    
    parts = authorization.split()

    if parts[0].lower() != "bearer" or len(parts) != 2:
        # Token formatı yanlışsa veya token yoksa devam et ama kullanıcı döndürme
        return None

    token = parts[1]
    
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    user = await auth_service.get_user(username=username)
    return user


@router.get("", response_model=List[MovieResponse])
async def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    movies = await MovieService.get_movies(user_id=user_id, skip=skip, limit=limit)
    return movies

@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    query: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    embedding = AIService.get_embedding_for_text(query)
    movies = await MovieService.search_movies_by_vector(embedding=embedding, user_id=user_id)
    return movies

@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    movie = await MovieService.get_movie_by_id(movie_id=movie_id, user_id=user_id)
    return movie

@router.get("/{movie_id}/similar", response_model=List[MovieResponse])
async def get_similar_movies(
    movie_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    similar_movies = await MovieService.get_similar_movies(movie_id=movie_id, user_id=user_id)
    return similar_movies 