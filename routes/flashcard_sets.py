from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Flashcard, FlashcardSet
from schemas import FlashcardSetCreate, FlashcardSetResponse, FlashcardSetUpdate

router = APIRouter()


@router.post("", response_model=FlashcardSetResponse, status_code=201)
def create_flashcard_set(
    data: FlashcardSetCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    flashcard_set = FlashcardSet(
        name=data.name,
        user_id=current_user["id"],
        language=data.language,
        source_type=data.source_type,
        journal_entry_id=data.journal_entry_id,
    )

    for card_data in data.flashcards:
        flashcard = Flashcard(
            front=card_data.front,
            back=card_data.back,
            language=card_data.language or data.language,
        )

        flashcard_set.flashcards.append(flashcard)

    db.add(flashcard_set)
    db.commit()
    db.refresh(flashcard_set)

    return flashcard_set


@router.get("", response_model=list[FlashcardSetResponse])
def get_flashcard_sets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(FlashcardSet)
        .filter(FlashcardSet.user_id == current_user["id"],)
        .order_by(FlashcardSet.created_at.desc())
        .all()
    )


@router.get(
    "/{flashcard_set_id}",
    response_model=FlashcardSetResponse,
)
def get_flashcard_set(
    flashcard_set_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.id == flashcard_set_id, 
            FlashcardSet.user_id == current_user["id"],)
        .first()
    )

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    return flashcard_set


@router.delete("/{flashcard_set_id}", status_code=204)
def delete_flashcard_set(
    flashcard_set_id: int,
    db: Session = Depends(get_db),
):
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(FlashcardSet.id == flashcard_set_id)
        .first()
    )

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    db.delete(flashcard_set)
    db.commit()


@router.patch(
    "/{flashcard_set_id}",
    response_model=FlashcardSetResponse,
)
def update_flashcard_set(
    flashcard_set_id: int,
    data: FlashcardSetUpdate,
    db: Session = Depends(get_db),
):
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(FlashcardSet.id == flashcard_set_id)
        .first()
    )

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(flashcard_set, field, value)

    db.commit()
    db.refresh(flashcard_set)

    return flashcard_set