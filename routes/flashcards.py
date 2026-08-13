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


router = APIRouter()


@router.post("", response_model=FlashcardResponse, status_code=201)
def create_flashcard(
    data: FlashcardCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    
):
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

    return flashcard

@router.get("", response_model=list[FlashcardResponse])
def get_flashcards(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(Flashcard)
    .filter(
        Flashcard.user_id == current_user["id"]
    )
    .order_by(Flashcard.created_at.desc())
    .all()
)


@router.patch("/{flashcard_id}", response_model=FlashcardResponse)
def update_flashcard(
    flashcard_id: int,
    data: FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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

    return flashcard


@router.delete("/{flashcard_id}", status_code=204)
def delete_flashcard(
    flashcard_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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
