from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ContentBase(BaseModel):
    title: str
    type: Literal["movie", "series"]
    genres: List[str]
    description: str
    release_year: int
    image_url: Optional[str] = None


class ContentCreate(ContentBase):
    pass


class ContentInDB(ContentBase):
    id: str = Field(alias="_id")
