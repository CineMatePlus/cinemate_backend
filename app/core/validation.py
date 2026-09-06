from typing import Annotated

from bson import ObjectId
from fastapi import HTTPException
from pydantic import StringConstraints

NameText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
CommentText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]
DescriptionText = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=2000)
]


def object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(value)
