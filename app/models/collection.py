from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.validation import DescriptionText, NameText
from app.models.pyobjectid import PyObjectId


class CollectionBase(BaseModel):
    """Koleksiyon temel modeli"""

    name: NameText
    description: Optional[DescriptionText] = None
    is_public: bool = True


class CollectionCreate(CollectionBase):
    """Koleksiyon oluşturma modeli"""

    pass


class CollectionUpdate(BaseModel):
    """Koleksiyon güncelleme modeli"""

    name: Optional[NameText] = None
    description: Optional[DescriptionText] = None
    is_public: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data):
        if isinstance(data, dict) and any(
            key in data and data[key] is None for key in ("name", "is_public")
        ):
            raise ValueError("name and is_public cannot be null")
        return data


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

    owner_name: NameText
    movie_count: int = 0
