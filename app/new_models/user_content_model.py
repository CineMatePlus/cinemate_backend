from pydantic import BaseModel


class UserContent(BaseModel):
    user_id: str
    content_id: str
    collection_id: str
    watched: bool = False
