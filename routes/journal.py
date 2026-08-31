from fastapi import APIRouter, Depends, HTTPException

from services.correction_service import correct_text
from services.correction_service import add_indices

from schemas import (
    JournalAnalysisRequest,
    JournalAnalysisResponse,
    JournalEntryResponse,
    JournalEntryUpdate,
)

from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import JournalEntry, UserActivity
from badge_service import evaluate_progress_badges


router = APIRouter()


# ------------------------------------------------------------------
# Analyze journal entry
# ------------------------------------------------------------------

@router.post("/analyze", response_model=JournalAnalysisResponse)
async def analyze_journal(
    data: JournalAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    title = data.title
    text = data.text
    native_language = data.native_language
    target_language = data.target_language
    review_depth = data.review_depth

    print(f"Review depth: {review_depth}")

    # Run the selected correction implementation.
    analysis = await correct_text(
        text=text,
        native_language=native_language,
        target_language=target_language,
        review_depth=review_depth,
    )

    # Add character positions for frontend highlighting.
    analysis = add_indices(
        text,
        analysis,
    )

    # Make sure accuracy always exists.
    accuracy = analysis.get("accuracy")

    if not isinstance(accuracy, dict):
        accuracy = {
            "score": 0,
            "summary": "",
            "categories": {
                "grammar": 0,
                "vocabulary": 0,
                "spelling": 0,
                "sentenceStructure": 0,
            },
            "improvementNote": "",
        }

        analysis["accuracy"] = accuracy

    # --------------------------------------------------------------
    # Save journal entry
    # --------------------------------------------------------------

    journal_entry = JournalEntry(
        title=title,
        user_id=current_user["id"],
        original_text=text,
        target_language=target_language,
        corrected_text=analysis["text"],
        mistakes=analysis["mistakes"],
    )

    db.add(journal_entry)
    db.commit()
    db.refresh(journal_entry)

    # --------------------------------------------------------------
    # Record activity
    # --------------------------------------------------------------

    activity = UserActivity(
        user_id=current_user["id"],
        activity_type="journal_analyzed",
        activity_data={
            "accuracy_score": accuracy.get("score", 0),
            "target_language": target_language,
            "review_depth": review_depth,
        },
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    # --------------------------------------------------------------
    # Evaluate badges
    # --------------------------------------------------------------

    evaluate_progress_badges(
        user_id=current_user["id"],
        db=db,
    )

    # --------------------------------------------------------------
    # Add response metadata
    # --------------------------------------------------------------

    analysis["title"] = title
    analysis["journal_entry_id"] = journal_entry.id

    return analysis


# ------------------------------------------------------------------
# Get journal entries
# ------------------------------------------------------------------

@router.get(
    "/entries",
    response_model=list[JournalEntryResponse],
)
def get_journal_entries(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.user_id == current_user["id"]
        )
        .order_by(
            JournalEntry.created_at.desc()
        )
        .all()
    )


# ------------------------------------------------------------------
# Get journal statistics
# ------------------------------------------------------------------

@router.get("/stats")
def get_journal_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lifetime_journal_count = (
        db.query(UserActivity)
        .filter(
            UserActivity.user_id == current_user["id"],
            UserActivity.activity_type == "journal_analyzed",
        )
        .count()
    )

    return {
        "lifetime_journal_count": lifetime_journal_count
    }


# ------------------------------------------------------------------
# Delete journal entry
# ------------------------------------------------------------------

@router.delete("/{entry_id}")
def delete_journal_entry(
    entry_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    journal_entry = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user["id"],
        )
        .first()
    )

    if not journal_entry:
        raise HTTPException(
            status_code=404,
            detail="Journal entry not found",
        )

    db.delete(journal_entry)
    db.commit()

    return {
        "message": "Journal entry deleted successfully"
    }


# ------------------------------------------------------------------
# Update journal entry
# ------------------------------------------------------------------

@router.put(
    "/{entry_id}",
    response_model=JournalEntryResponse,
)
async def update_journal_entry(
    entry_id: int,
    data: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    journal_entry = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user["id"],
        )
        .first()
    )

    if not journal_entry:
        raise HTTPException(
            status_code=404,
            detail="Journal entry not found",
        )

    # --------------------------------------------------------------
    # Re-analyze edited writing
    # --------------------------------------------------------------

    analysis = await correct_text(
        text=data.original_text,
        native_language=current_user.get(
            "native_language",
            "English",
        ),
        target_language=data.target_language,
        review_depth=data.review_depth,
    )

    # Add indices for frontend highlighting.
    analysis = add_indices(
        data.original_text,
        analysis,
    )

    # --------------------------------------------------------------
    # Update existing journal entry
    # --------------------------------------------------------------

    journal_entry.title = data.title
    journal_entry.original_text = data.original_text
    journal_entry.target_language = data.target_language
    journal_entry.corrected_text = analysis["text"]
    journal_entry.mistakes = analysis["mistakes"]

    db.commit()
    db.refresh(journal_entry)

    return journal_entry

