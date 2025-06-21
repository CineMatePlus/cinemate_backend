from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class MovieBase(BaseModel):
    title: str
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    status: Optional[str] = None
    release_date: Optional[date] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    adult: Optional[bool] = False
    backdrop_path: Optional[str] = None
    budget: Optional[int] = None
    homepage: Optional[str] = None
    imdb_id: Optional[str] = None
    original_language: Optional[str] = None
    original_title: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    tagline: Optional[str] = None
    genres: Optional[List[str]] = None
    production_companies: Optional[List[str]] = None
    production_countries: Optional[List[str]] = None
    spoken_languages: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    num_likes: int = 0
    num_watches: int = 0


class MovieCreate(MovieBase):
    embedding: Optional[List[float]] = None


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    status: Optional[str] = None
    release_date: Optional[date] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    adult: Optional[bool] = None
    backdrop_path: Optional[str] = None
    budget: Optional[int] = None
    homepage: Optional[str] = None
    imdb_id: Optional[str] = None
    original_language: Optional[str] = None
    original_title: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    tagline: Optional[str] = None
    genres: Optional[List[str]] = None
    production_companies: Optional[List[str]] = None
    production_countries: Optional[List[str]] = None
    spoken_languages: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    num_likes: Optional[int] = None
    num_watches: Optional[int] = None


class MovieInDB(MovieBase):
    id: str = Field(..., alias="_id")
    embedding: Optional[List[float]] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class MovieResponse(MovieBase):
    id: str = Field(..., alias="_id")
    is_liked: bool = False
    is_watched: bool = False
    is_in_watchlist: bool = False

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
