from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CollectionBase(BaseModel):
    """Koleksiyon temel modeli"""

    title: str = Field(..., min_length=1, max_length=100)
    is_public: bool = Field(default=True)


class CollectionCreate(CollectionBase):
    """Koleksiyon oluşturma modeli"""

    pass


class CollectionUpdate(CollectionBase):
    """Koleksiyon güncelleme modeli"""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    is_public: Optional[bool] = None


class CollectionInDB(CollectionBase):
    """Veritabanı koleksiyon modeli"""

    id: str = Field(..., alias="_id")
    user_id: str
    content_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True


class CollectionResponse(CollectionBase):
    """Koleksiyon yanıt modeli"""

    id: str = Field(..., alias="_id")
    user_id: str
    content_ids: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
