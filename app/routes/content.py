from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.content_model import ContentCreate, ContentInDB
from app.database.mongo import db
from bson import ObjectId


content_router = APIRouter(prefix="/content", tags=["Content"])


@content_router.post("/")
async def create_content(content: ContentCreate):
    result = await db["contents"].insert_one(content.dict())
    return {"id": str(result.inserted_id)}


@content_router.get("/search", response_model=List[ContentInDB])
async def search_content(
    q: Optional[str] = None,
    type: Optional[str] = Query(None, regex="^(movie|series)$"),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
):
    query = {}

    if q:
        query["title"] = {"$regex": q, "$options": "i"}
    if type:
        query["type"] = type
    if genre:
        query["genres"] = genre
    if year:
        query["release_year"] = year
    else:
        if year_min or year_max:
            query["release_year"] = {}
        if year_min:
            query["release_year"]["$gte"] = year_min
        if year_max:
            query["release_year"]["$lte"] = year_max

    contents_cursor = db["contents"].find(query)
    contents = await contents_cursor.to_list(length=None)
    return [{**item, "_id": str(item["_id"])} for item in contents]


@content_router.get("/", response_model=List[ContentInDB])
async def list_contents():
    contents_cursor = db["contents"].find()
    contents = await contents_cursor.to_list(length=None)
    return [{**item, "_id": str(item["_id"])} for item in contents]


@content_router.get("/{content_id}", response_model=ContentInDB)
async def get_content(content_id: str):
    content = await db["contents"].find_one({"_id": ObjectId(content_id)})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    content["_id"] = str(content["_id"])
    return content
