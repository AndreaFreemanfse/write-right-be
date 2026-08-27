from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Flashcard, FlashcardSet, JournalEntry
from schemas import (
    FlashcardSetCreate,
    FlashcardSetResponse,
    FlashcardSetSaveResponse,
    FlashcardSetUpdate,
)
from badge_service import evaluate_progress_badges
import time

router = APIRouter()


@router.post("", response_model=FlashcardSetSaveResponse)
def create_flashcard_set(
    data: FlashcardSetCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    # Journal-generated sets must belong to a journal owned by this user.
    if data.journal_entry_id is not None:
        journal_entry = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.id == data.journal_entry_id,
                JournalEntry.user_id == current_user["id"],
            )
            .first()
        )

        if journal_entry is None:
            raise HTTPException(
                status_code=404,
                detail="Journal entry not found",
            )

    normalized_name = data.name.strip().casefold()

    # For the current user, journal sets with the same normalized title
    # are treated as the same flashcard set.
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.user_id == current_user["id"],
            FlashcardSet.source_type == "journal",
            func.lower(func.trim(FlashcardSet.name)) == normalized_name,
        )
        .first()
    )

    created = False

    # Create a set only when this user does not already have a
    # journal-generated set with the same title.
    if flashcard_set is None:
        created = True

        flashcard_set = FlashcardSet(
            name=data.name.strip(),
            user_id=current_user["id"],
            language=data.language,
            source_type=data.source_type,
            journal_entry_id=data.journal_entry_id,
        )

        db.add(flashcard_set)
        db.flush()

    # Build a normalized collection of cards already in the set.
    existing_cards = {
        (
            card.front.strip().casefold(),
            card.back.strip().casefold(),
        )
        for card in flashcard_set.flashcards
    }

    added_count = 0

    # Append only cards that are not already in the set.
    for card_data in data.flashcards:
        card_key = (
            card_data.front.strip().casefold(),
            card_data.back.strip().casefold(),
        )

        if card_key in existing_cards:
            continue

        flashcard = Flashcard(
            user_id=current_user["id"],
            set_id=flashcard_set.id,
            front=card_data.front.strip(),
            back=card_data.back.strip(),
            language=card_data.language or data.language,
        )

        flashcard_set.flashcards.append(flashcard)
        existing_cards.add(card_key)
        added_count += 1

    db.commit()
    db.refresh(flashcard_set)
    evaluate_progress_badges(
        user_id=current_user["id"],
        db=db,
    )

    if created:
        message = (
            f"Flashcard set created with {added_count} "
            f"new card{'s' if added_count != 1 else ''}."
        )
    elif added_count > 0:
        message = (
            f"{added_count} new flashcard"
            f"{'s were' if added_count != 1 else ' was'} "
            "added to the existing set."
        )
    else:
        message = "No new flashcards were added because they already exist."

    result = {
        "flashcard_set": flashcard_set,
        "created": created,
        "added_count": added_count,
        "message": message,
    }
    print(f"[TIMING] flashcard_sets_create completed in {(time.time() - start_time) * 1000:.2f}ms")
    return result


@router.get("", response_model=list[FlashcardSetResponse])
def get_flashcard_sets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    result = (
        db.query(FlashcardSet)
        .filter(FlashcardSet.user_id == current_user["id"])
        .order_by(FlashcardSet.created_at.desc())
        .all()
    )
    print(f"[TIMING] flashcard_sets_get_all completed in {(time.time() - start_time) * 1000:.2f}ms")
    return result


@router.get(
    "/{flashcard_set_id}",
    response_model=FlashcardSetResponse,
)
def get_flashcard_set(
    flashcard_set_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.id == flashcard_set_id,
            FlashcardSet.user_id == current_user["id"],
        )
        .first()
    )

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    print(f"[TIMING] flashcard_sets_get_one completed in {(time.time() - start_time) * 1000:.2f}ms")
    return flashcard_set


@router.delete("/{flashcard_set_id}", status_code=204)
def delete_flashcard_set(
    flashcard_set_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.id == flashcard_set_id,
            FlashcardSet.user_id == current_user["id"],
        )
        .first()
    )

    if flashcard_set is None:
        raise HTTPException(
            status_code=404,
            detail="Flashcard set not found",
        )

    db.delete(flashcard_set)
    db.commit()
    print(f"[TIMING] flashcard_sets_delete completed in {(time.time() - start_time) * 1000:.2f}ms")

@router.patch(
    "/{flashcard_set_id}",
    response_model=FlashcardSetResponse,
)
def update_flashcard_set(
    flashcard_set_id: int,
    data: FlashcardSetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start_time = time.time()
    flashcard_set = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.id == flashcard_set_id,
            FlashcardSet.user_id == current_user["id"],
        )
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

    print(f"[TIMING] flashcard_sets_update completed in {(time.time() - start_time) * 1000:.2f}ms")
    return flashcard_set