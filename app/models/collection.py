from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.movie import MovieResponse


class CollectionBase(BaseModel):
    """Koleksiyon temel modeli"""

    name: str
    description: Optional[str] = None
    is_public: bool = True


class CollectionCreate(CollectionBase):
    """Koleksiyon oluşturma modeli"""

    pass


class CollectionUpdate(BaseModel):
    """Koleksiyon güncelleme modeli"""

    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CollectionInDB(CollectionBase):
    """Veritabanı koleksiyon modeli"""

    id: str = Field(..., alias="_id")
    user_id: str
    movie_ids: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class CollectionResponse(CollectionInDB):
    """Koleksiyon yanıt modeli"""

    owner_name: str
    movies: List[MovieResponse] = []

    class Config:
        allow_population_by_field_name = True
