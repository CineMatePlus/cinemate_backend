from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ContentBase(BaseModel):
    title: str
    description: str
    genres: List[str]
    year: int


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None
    year: Optional[int] = None


class ContentInDB(ContentBase):
    id: str = Field(..., alias="_id")
    average_rating: float = 0.0
    num_likes: int = 0
    num_watches: int = 0
    num_ratings: int = 0
    num_comments: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ContentResponse(ContentBase):
    id: str = Field(..., alias="_id")
    average_rating: float
    num_likes: int
    num_watches: int
    num_ratings: int
    num_comments: int
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
