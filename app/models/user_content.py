from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserContentBase(BaseModel):
    user_id: str
    content_id: str
    is_liked: bool = False
    is_watched: bool = False
    in_watchlist: bool = False
    rated: Optional[int] = None


class UserContentCreate(UserContentBase):
    pass


class UserContentUpdate(BaseModel):
    is_liked: Optional[bool] = None
    is_watched: Optional[bool] = None
    in_watchlist: Optional[bool] = None
    rated: Optional[int] = None


class UserContentInDB(UserContentBase):
    id: str = Field(..., alias="_id")
    last_interacted_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserContentResponse(UserContentBase):
    id: str = Field(..., alias="_id")
    last_interacted_at: datetime
    content: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
