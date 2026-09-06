from datetime import datetime
from enum import IntEnum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Gender(IntEnum):
    """
    Kullanıcı cinsiyet bilgisini tutan enum sınıfı.
    MongoDB'de integer olarak saklanır:
    - 0: Kadın (Female)
    - 1: Erkek (Male)
    - 2: Diğer (Other)
    """

    FEMALE = 0
    MALE = 1
    OTHER = 2


class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    gender: Gender = Gender.OTHER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[Gender] = None


class UserInDB(UserBase):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda dt: dt.isoformat(), IntEnum: lambda v: int(v)},
    )

    id: str = Field(alias="_id")
    hashed_password: str
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat(), IntEnum: lambda v: int(v)},
    )

    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime


class PublicUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    name: str
    avatar_url: Optional[str] = None
    gender: Gender = Gender.OTHER
    created_at: datetime
    updated_at: datetime


class SimilarUserResponse(PublicUserResponse):
    similarity: float
