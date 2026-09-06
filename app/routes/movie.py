from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.models.movie import MovieResponse
from app.models.user import UserInDB
from app.services.auth import AuthService
from app.services.embedding import EmbeddingProviderError, get_embedding_service
from app.services.movie import MovieService

router = APIRouter(tags=["movies"])
auth_service = AuthService()


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[UserInDB]:
    if authorization is None:
        return None

    token = auth_service.bearer_token(authorization)
    return await auth_service.get_current_user(token)


@router.get("", response_model=List[MovieResponse])
async def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    movies = await MovieService.get_movies(user_id=user_id, skip=skip, limit=limit)
    return movies


@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    q: str = Query(..., alias="query", min_length=1, max_length=500, pattern=r".*\S.*"),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    try:
        embedding = await get_embedding_service().embed_query(q)
    except EmbeddingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Arama servisi geçici olarak kullanılamıyor. Tekrar deneyin.",
        ) from exc
    movies = await MovieService.search_movies_by_vector(
        embedding=embedding, user_id=user_id, limit=limit
    )
    return movies


@router.get("/genre/{genre}", response_model=List[MovieResponse])
async def get_movies_by_genre(
    genre: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    movies = await MovieService.get_movies_by_genre(
        genre=genre, user_id=user_id, skip=skip, limit=limit
    )
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: str, current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    movie = await MovieService.get_movie_by_id(movie_id=movie_id, user_id=user_id)
    return movie


@router.get("/{movie_id}/similar", response_model=List[MovieResponse])
async def get_similar_movies(
    movie_id: str, current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    similar_movies = await MovieService.get_similar_movies(
        movie_id=movie_id, user_id=user_id
    )
    return similar_movies
