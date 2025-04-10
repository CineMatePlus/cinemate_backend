from pydantic import BaseModel, EmailStr


class UserIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    access_token: str
    refresh_token: str


class UserInDB(BaseModel):
    email: EmailStr
    hashed_password: str
