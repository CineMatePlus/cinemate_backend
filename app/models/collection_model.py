from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal


class CollectionType(str, Enum):  # Enum kullanımı
    WATCHED = "watched"
    TO_WATCH = "to_watch"
    CUSTOM = "custom"


class CollectionBase(BaseModel):
    name: str
    type: CollectionType = CollectionType.CUSTOM  # Default "custom" tipi
    immutable: bool = False


class CollectionCreate(CollectionBase):
    pass


class CollectionInDB(CollectionBase):
    id: str = Field(alias="_id")
    user_id: str
