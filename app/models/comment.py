from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.validation import CommentText
from app.models.user import PublicUserResponse


class CommentBase(BaseModel):
    text: CommentText


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    text: CommentText


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
    user: PublicUserResponse
