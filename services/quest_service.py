from sqlalchemy.orm import Session
from schemas import QuestResponse
from services.ai_service import generate_quests

from models import JournalEntry


def get_quest_mistake_history(
    user_id: str,
    db: Session,
    limit: int = 10,
):
    journal_entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .all()
    )

    mistakes = []

    for entry in journal_entries:
        for mistake in entry.mistakes or []:
            mistakes.append(
                {
                    "original": mistake.get("original"),
                    "corrected": mistake.get("corrected"),
                    "original_full": mistake.get("original_full"),
                    "corrected_full": mistake.get("corrected_full"),
                    "explanation": mistake.get("explanation"),
                    "category": mistake.get("category"),
                    "target_language": entry.target_language,
                }
            )

    return mistakes

async def create_personalized_quests(
    user_id: str,
    db: Session,
):
    mistakes = get_quest_mistake_history(
        user_id=user_id,
        db=db,
    )

    if not mistakes:
        return None

    target_language = next(
        (
            mistake["target_language"]
            for mistake in mistakes
            if mistake.get("target_language")
        ),
        "English",
    )

    quest_data = await generate_quests(
        mistakes=mistakes,
        target_language=target_language,
    )

    return QuestResponse.model_validate(quest_data)