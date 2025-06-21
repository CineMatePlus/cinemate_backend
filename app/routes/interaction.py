from fastapi import APIRouter, Depends, status, HTTPException
from enum import Enum
from app.services.interaction import InteractionService
from app.models.user import UserInDB
from app.routes.collection import get_current_user_required

router = APIRouter(
    tags=["User Interactions"]
)

interaction_service = InteractionService()

class InteractionType(str, Enum):
    like = "like"
    watched = "watched"
    watchlist = "watchlist"

@router.post("/{movie_id}/{interaction_type}", status_code=status.HTTP_200_OK)
async def toggle_interaction(
    movie_id: str,
    interaction_type: InteractionType,
    current_user: UserInDB = Depends(get_current_user_required),
):
    """
    Toggles a user's interaction with a movie (like, watched, watchlist).
    
    - **movie_id**: The ID of the movie.
    - **interaction_type**: The type of interaction (`like`, `watched`, `watchlist`).
    """
    try:
        was_added = await interaction_service.toggle_interaction(
            user_id=current_user.id,
            movie_id=movie_id,
            interaction_type=interaction_type.value,
        )
        
        action = "added" if was_added else "removed"
        return {"status": "success", "action": action, "interaction": interaction_type.value}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
