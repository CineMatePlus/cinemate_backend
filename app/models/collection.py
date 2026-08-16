from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

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

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={PyObjectId: str, datetime: lambda v: v.isoformat()},
    )

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    movie_ids: List[PyObjectId] = []
    created_at: datetime
    updated_at: datetime


class CollectionResponse(CollectionInDB):
    """Koleksiyon yanıt modeli"""

    model_config = ConfigDict(populate_by_name=True)

    owner_name: str
    movie_count: int = 0
