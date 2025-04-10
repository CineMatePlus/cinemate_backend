from pydantic import BaseModel, EmailStr
from typing import List
from app.models.collection_model import CollectionInDB, CollectionType


class UserIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    access_token: str
    refresh_token: str
    collections: List[CollectionInDB] = []  # Kullanıcının koleksiyonları


class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str
    collections: List[CollectionInDB] = []  # Kullanıcının koleksiyonları

    def add_default_collections(self):
        default_collections = [
            CollectionInDB(
                name="İzlediklerim",
                type=CollectionType.WATCHED,
                immutable=True,
                user_id=self.id,
            ),
            CollectionInDB(
                name="İzleyeceklerim",
                type=CollectionType.TO_WATCH,
                immutable=True,
                user_id=self.id,
            ),
        ]
        self.collections.extend(default_collections)
