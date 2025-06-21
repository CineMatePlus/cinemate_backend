from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InteractionBase(BaseModel):
    user_id: str = Field(...)
    movie_id: str = Field(...)
    interaction_type: str = Field(
        ...,
        description="'like', 'watched', 'watchlist', veya 'collection_add' olabilir",
    )
    collection_id: Optional[str] = Field(
        None, description="Eğer interaction_type 'collection_add' ise zorunludur"
    )


class InteractionCreate(InteractionBase):
    pass


class InteractionInDB(InteractionBase):
    id: str = Field(..., alias="_id")
    created_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
