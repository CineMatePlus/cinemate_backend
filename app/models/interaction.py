from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .pyobjectid import PyObjectId


class InteractionBase(BaseModel):
    user_id: PyObjectId = Field(...)
    movie_id: PyObjectId = Field(...)
    interaction_type: str = Field(
        ...,
        description="'like', 'watched', 'watchlist', veya 'collection_add' olabilir",
    )
    collection_id: Optional[PyObjectId] = Field(
        None, description="Eğer interaction_type 'collection_add' ise zorunludur"
    )

    class Config:
        arbitrary_types_allowed = True


class InteractionCreate(InteractionBase):
    pass


class InteractionInDB(InteractionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
