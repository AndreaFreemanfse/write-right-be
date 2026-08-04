from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Badge, Flashcard, FlashcardSet, JournalEntry, UserBadge


BADGE_DEFINITIONS = [
    {
        "key": "first_steps",
        "name": "First Steps",
        "description": "Analyze your first journal.",
        "icon": "🥉",
    },
    {
        "key": "journal_explorer",
        "name": "Journal Explorer",
        "description": "Analyze 5 journals.",
        "icon": "📖",
    },
    {
        "key": "high_accuracy",
        "name": "High Accuracy",
        "description": "Earn a journal accuracy score of 90% or higher.",
        "icon": "🎯",
    },
    {
        "key": "perfect_journal",
        "name": "Perfect Journal",
        "description": "Earn a 100% journal accuracy score.",
        "icon": "💯",
    },
    {
        "key": "polyglot",
        "name": "Polyglot",
        "description": "Practice in 3 different target languages.",
        "icon": "🌍",
    },
    {
        "key": "streak_master",
        "name": "Streak Master",
        "description": "Analyze a journal on 7 consecutive days.",
        "icon": "🔥",
    },
    {
        "key": "vault_starter",
        "name": "Vault Starter",
        "description": "Create your first flashcard set.",
        "icon": "📚",
    },
    {
        "key": "vault_builder",
        "name": "Vault Builder",
        "description": "Create 6 flashcard sets.",
        "icon": "🏛️",
    },
    {
        "key": "card_collector",
        "name": "Card Collector",
        "description": "Save 25 flashcards.",
        "icon": "🃏",
    },
    {
        "key": "study_habit",
        "name": "Study Habit",
        "description": "Master 10 flashcards.",
        "icon": "🎓",
    },
    {
        "key": "word_hunter",
        "name": "Word Hunter",
        "description": "Complete 10 successful dictionary searches.",
        "icon": "🔍",
    },
]



def seed_badges(db: Session) -> None:
    existing_keys = {
        key
        for (key,) in db.query(Badge.key).all()
    }

    for definition in BADGE_DEFINITIONS:
        if definition["key"] in existing_keys:
            continue

        db.add(Badge(**definition))

    db.commit()


def award_badge(
    user_id,
    badge_key: str,
    db: Session,
) -> UserBadge | None:
    badge = (
        db.query(Badge)
        .filter(Badge.key == badge_key)
        .first()
    )

    if badge is None:
        return None

    existing_user_badge = (
        db.query(UserBadge)
        .filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
        .first()
    )

    if existing_user_badge is not None:
        return None

    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id,
    )

    db.add(user_badge)
    db.commit()
    db.refresh(user_badge)
    print(
        f"🏅 Awarded '{badge.name}' to user {user_id}"
    )

    return user_badge


def evaluate_progress_badges(
    user_id,
    db: Session,
) -> list[UserBadge]:
    seed_badges(db)

    newly_earned = []

    journal_count = (
        db.query(func.count(JournalEntry.id))
        .filter(JournalEntry.user_id == user_id)
        .scalar()
        or 0
    )

    flashcard_set_count = (
        db.query(func.count(FlashcardSet.id))
        .filter(FlashcardSet.user_id == user_id)
        .scalar()
        or 0
    )

    flashcard_count = (
        db.query(func.count(Flashcard.id))
        .filter(Flashcard.user_id == user_id)
        .scalar()
        or 0
    )

    mastered_count = (
        db.query(func.count(Flashcard.id))
        .filter(
            Flashcard.user_id == user_id,
            Flashcard.mastered.is_(True),
        )
        .scalar()
        or 0
    )

    badge_rules = [
        (journal_count >= 1, "first_steps"),
        (journal_count >= 5, "journal_explorer"),
        (flashcard_set_count >= 1, "vault_starter"),
        (flashcard_set_count >= 6, "vault_builder"),
        (flashcard_count >= 25, "card_collector"),
        (mastered_count >= 10, "study_habit"),
    ]

    for qualifies, badge_key in badge_rules:
        if not qualifies:
            continue

        awarded = award_badge(
            user_id=user_id,
            badge_key=badge_key,
            db=db,
        )

        if awarded is not None:
            newly_earned.append(awarded)

    return newly_earned