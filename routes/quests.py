from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from schemas import QuestResponse
from services.quest_service import create_personalized_quests


router = APIRouter(
    prefix="/quests",
    tags=["quests"],
)


@router.post("/generate", response_model=QuestResponse)
async def generate_personalized_quests(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quests = await create_personalized_quests(
        user_id=current_user["id"],
        db=db,
    )

    if quests is None:
        raise HTTPException(
            status_code=400,
            detail="Not enough journal history to generate quests.",
        )

    return quests