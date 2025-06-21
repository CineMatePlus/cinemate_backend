from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserResponse


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    text: Optional[str] = None


class CommentInDB(CommentBase):
    id: str = Field(..., alias="_id")
    movie_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class CommentData(CommentBase):
    id: str = Field(..., alias="_id")
    movie_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class CommentResponse(BaseModel):
    comment: CommentData
    user: UserResponse

    class Config:
        allow_population_by_field_name = True
