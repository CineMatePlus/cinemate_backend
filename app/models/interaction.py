from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from .pyobjectid import PyObjectId


class InteractionBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: PyObjectId = Field(...)
    movie_id: PyObjectId = Field(...)
    interaction_type: str = Field(
        ...,
        description="'like', 'watched', 'watchlist', veya 'collection_add' olabilir",
    )
    collection_id: Optional[PyObjectId] = Field(
        None, description="Eğer interaction_type 'collection_add' ise zorunludur"
    )


class InteractionCreate(InteractionBase):
    pass


class InteractionInDB(InteractionBase):
    model_config = ConfigDict(populate_by_name=True, json_encoders={ObjectId: str})

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
