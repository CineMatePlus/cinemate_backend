from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.movie import MovieResponse
from app.models.pyobjectid import PyObjectId


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

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    movie_ids: List[PyObjectId] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}


class CollectionResponse(CollectionInDB):
    """Koleksiyon yanıt modeli"""

    owner_name: str
    movie_count: int = 0

    class Config:
        allow_population_by_field_name = True
