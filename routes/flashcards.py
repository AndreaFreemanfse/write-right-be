from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user

from database import get_db
from models import Flashcard, FlashcardSet
from schemas import (
    FlashcardCreate,
    FlashcardResponse,
    FlashcardUpdate
)
from badge_service import evaluate_progress_badges
import time

router = APIRouter()


@router.post("", response_model=FlashcardResponse, status_code=201)
def create_flashcard(
    data: FlashcardCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),

):
    start_time = time.time()
    flashcard_set = (
    db.query(FlashcardSet)
    .filter(
        FlashcardSet.id == data.set_id,
        FlashcardSet.user_id == current_user["id"],
    )
    .first()
)

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    flashcard = Flashcard(
        user_id=current_user["id"],
        set_id=data.set_id,
        front=data.front,
        back=data.back,
        language=data.language,
    )

    db.add(flashcard)
    db.commit()
    db.refresh(flashcard)
    evaluate_progress_badges(
        user_id=current_user["id"],
        db=db,
    )

    print(f"[TIMING] flashcards_create completed in {(time.time() - start_time) * 1000:.2f}ms")
    return flashcard

@router.get("", response_model=list[FlashcardResponse])
def get_flashcards(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    result = (
        db.query(Flashcard)
    .filter(
        Flashcard.user_id == current_user["id"]
    )
    .order_by(Flashcard.created_at.desc())
    .all()
)
    print(f"[TIMING] flashcards_get_all completed in {(time.time() - start_time) * 1000:.2f}ms")
    return result


@router.patch("/{flashcard_id}", response_model=FlashcardResponse)
def update_flashcard(
    flashcard_id: int,
    data: FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    flashcard = (
        db.query(Flashcard)
        .filter(
            Flashcard.id == flashcard_id,
            Flashcard.user_id == current_user["id"],
        )
        .first()
    )

    if flashcard is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(flashcard, key, value)

    db.commit()
    db.refresh(flashcard)
    evaluate_progress_badges(
        user_id=current_user["id"],
        db=db,
    )

    print(f"[TIMING] flashcards_update completed in {(time.time() - start_time) * 1000:.2f}ms")
    return flashcard


@router.delete("/{flashcard_id}", status_code=204)
def delete_flashcard(
    flashcard_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    flashcard = (
        db.query(Flashcard)
        .filter(
            Flashcard.id == flashcard_id,
            Flashcard.user_id == current_user["id"],
        )
        .first()
    )

    if flashcard is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard not found",
        )

    db.delete(flashcard)
    db.commit()
    print(f"[TIMING] flashcards_delete completed in {(time.time() - start_time) * 1000:.2f}ms")
