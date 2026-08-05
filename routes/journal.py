from fastapi import APIRouter, Depends
from services.ai_service import correct_text
from services.correction_service import add_indices
from schemas import (
    JournalAnalysisRequest,
    JournalAnalysisResponse,
    JournalEntryResponse,
)
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from models import JournalEntry, UserActivity
from badge_service import evaluate_progress_badges

router = APIRouter()


@router.post("/analyze", response_model=JournalAnalysisResponse)
async def analyze_journal(
    data: JournalAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    text = data.text
    native_language = data.native_language
    target_language = data.target_language 

    # AI anlysis of the text
    analysis = await correct_text(text, native_language, target_language)
    
    #Backend adds start/end indices to each mistake for frontend highlighting
    analysis = add_indices(
        text,
        analysis
    )

    journal_entry = JournalEntry(
        user_id=current_user["id"],
        original_text=text,
        target_language=target_language,
        corrected_text=analysis["text"],
        mistakes=analysis["mistakes"],
    )

    db.add(journal_entry)
    db.commit()
    db.refresh(journal_entry)

    activity = UserActivity(
        user_id=current_user["id"],
        activity_type="journal_analyzed",
        activity_data={
            "accuracy_score": analysis["accuracy"]["score"],
            "target_language": target_language,
        },
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    evaluate_progress_badges(
        user_id=current_user["id"],
        db=db,
    )

    analysis["journal_entry_id"] = journal_entry.id

    return analysis


@router.get("/entries", response_model=list[JournalEntryResponse])
def get_journal_entries(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == current_user["id"])
        .order_by(JournalEntry.created_at.desc())
        .all()
    )
