from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserResponse


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    text: Optional[str] = None


class CommentInDB(CommentBase):
    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(..., alias="_id")
    movie_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class CommentData(CommentBase):
    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(..., alias="_id")
    movie_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class CommentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    comment: CommentData
    user: UserResponse
