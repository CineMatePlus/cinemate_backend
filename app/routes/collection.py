from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId
from app.models.collection import (
    CollectionResponse,
    CollectionCreate,
    CollectionUpdate,
)
from app.services.collection import CollectionService
from app.models.user import UserInDB
from app.routes.movie import get_current_user_optional

router = APIRouter(tags=["collections"])

# Servis örneği
collection_service = CollectionService()

# Dependency for required authentication
async def get_current_user_required(user: Optional[UserInDB] = Depends(get_current_user_optional)):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection: CollectionCreate,
    current_user: UserInDB = Depends(get_current_user_required),
):
    created_collection = await collection_service.create_collection(
        collection=collection, user_id=current_user.id
    )
    # Refetch to populate movies and owner_name
    return await collection_service.get_collection_by_id(created_collection.id, current_user.id)

@router.get("/me", response_model=List[CollectionResponse])
async def get_my_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user_required),
):
    return await collection_service.get_user_collections(
        user_id=current_user.id, current_user_id=current_user.id, skip=skip, limit=limit
    )

@router.get("/user/{user_id}", response_model=List[CollectionResponse])
async def get_user_collections(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    current_user_id = current_user.id if current_user else None
    return await collection_service.get_user_collections(
        user_id=user_id, current_user_id=current_user_id, skip=skip, limit=limit
    )

@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    current_user_id = current_user.id if current_user else None
    return await collection_service.get_collection_by_id(collection_id, current_user_id)

@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection_update: CollectionUpdate,
    current_user: UserInDB = Depends(get_current_user_required),
):
    await collection_service.update_collection(
        collection_id=collection_id,
        collection_update=collection_update,
        user_id=current_user.id,
    )
    return await collection_service.get_collection_by_id(collection_id, current_user.id)

@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: UserInDB = Depends(get_current_user_required),
):
    await collection_service.delete_collection(
        collection_id=collection_id, user_id=current_user.id
    )
    return None

@router.post("/{collection_id}/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_movie_to_collection(
    collection_id: str,
    movie_id: str,
    current_user: UserInDB = Depends(get_current_user_required),
):
    await collection_service.add_movie_to_collection(
        collection_id=collection_id,
        movie_id=movie_id,
        user_id=current_user.id,
    )
    return None

@router.delete("/{collection_id}/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_movie_from_collection(
    collection_id: str,
    movie_id: str,
    current_user: UserInDB = Depends(get_current_user_required),
):
    await collection_service.remove_movie_from_collection(
        collection_id=collection_id,
        movie_id=movie_id,
        user_id=current_user.id,
    )
    return None
