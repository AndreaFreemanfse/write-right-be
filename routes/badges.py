from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user
from badge_service import seed_badges
from database import get_db
from models import UserBadge
from schemas import UserBadgeResponse
import time

router = APIRouter()


@router.get("", response_model=list[UserBadgeResponse])
def get_user_badges(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    seed_badges(db)

    result = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == current_user["id"])
        .order_by(UserBadge.earned_at.desc())
        .all()
    )
    print(f"[TIMING] badges_get_all completed in {(time.time() - start_time) * 1000:.2f}ms")
    return result