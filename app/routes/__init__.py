"""
API Routes
"""

from fastapi import APIRouter
from app.routes import auth, collection, content, comment, user_content

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    collection.router, prefix="/collections", tags=["collections"]
)
api_router.include_router(content.router, prefix="/contents", tags=["contents"])
api_router.include_router(comment.router, prefix="/comments", tags=["comments"])
api_router.include_router(
    user_content.router, prefix="/user-contents", tags=["user-contents"]
)
