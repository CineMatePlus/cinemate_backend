from pydantic import BaseModel, Field
from typing import Literal


class CollectionType(str):
    WATCHED = "watched"
    TO_WATCH = "to_watch"
    CUSTOM = "custom"


class CollectionBase(BaseModel):
    name: str
    type: Literal["watched", "to_watch", "custom"] = "custom"
    immutable: bool = False


class CollectionCreate(CollectionBase):
    pass


class CollectionInDB(CollectionBase):
    id: str = Field(alias="_id")
    user_id: str
