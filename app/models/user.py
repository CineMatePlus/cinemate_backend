from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from enum import IntEnum


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
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            IntEnum: lambda v: int(v)
        }


class UserResponse(UserBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            IntEnum: lambda v: int(v)
        }
