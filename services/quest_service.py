from sqlalchemy.orm import Session
from schemas import QuestResponse


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


def make_fill_blank(mistake):
    corrected = mistake.get("corrected")
    corrected_full = mistake.get("corrected_full")
    explanation = mistake.get("explanation")

    if not corrected:
        return None

    if corrected_full:
        marked_answer = f"**{corrected}**"

        if marked_answer in corrected_full:
            sentence = corrected_full.replace(
                marked_answer,
                "___",
                1,
            )
        else:
            sentence = corrected_full.replace(
                corrected,
                "___",
                1,
            )

        sentence = sentence.replace("**", "")
    else:
        sentence = "___"

    return {
        "sentence": sentence,
        "answer": corrected,
        "hint": "Use the correction from one of your previous journal mistakes.",
        "explanation": (
            explanation
            or f'The correct form is "{corrected}".'
        ),
    }


def usable_mistakes(mistakes):
    return [
        mistake
        for mistake in mistakes
        if mistake.get("original")
        and mistake.get("corrected")
        and mistake.get("original") != mistake.get("corrected")
    ]

async def create_personalized_quests(
    user_id: str,
    target_language: str,
    db: Session,
):
    mistakes = get_quest_mistake_history(
        user_id=user_id,
        db=db,
    )

    mistakes = usable_mistakes(mistakes)

    if not mistakes:
        return None

    mistakes = [
    mistake
    for mistake in mistakes
    if (
        mistake.get("target_language")
        and mistake["target_language"].lower()
        == target_language.lower()
    )
]

    if not mistakes:
        return None

    fill_blank = make_fill_blank(mistakes[0])

    spelling_candidates = [
        mistake
        for mistake in mistakes
        if (
            mistake.get("category")
            and "spell" in mistake["category"].lower()
        )
    ]

    # Fall back to any useful corrections if there are not
    # enough explicitly categorized spelling mistakes.
    remaining = [
        mistake
        for mistake in mistakes
        if mistake not in spelling_candidates
    ]

    spelling_candidates.extend(remaining)

    spelling_items = [
        {
            "word": mistake["corrected"],
            "clue": (
                mistake.get("explanation")
                or f'Previously corrected from "{mistake["original"]}".'
            ),
        }
        for mistake in spelling_candidates[:3]
    ]

    matching_pairs = []
    seen_prompts = set()
    seen_matches = set()

    for mistake in mistakes:
        prompt = mistake["original"].strip()
        match = mistake["corrected"].strip()

        prompt_key = prompt.lower()
        match_key = match.lower()

        if prompt_key in seen_prompts:
            continue

        if match_key in seen_matches:
            continue

        seen_prompts.add(prompt_key)
        seen_matches.add(match_key)

        matching_pairs.append(
            {
                "prompt": prompt,
                "match": match,
            }
        )

        if len(matching_pairs) == 4:
            break

    focus_areas = []

    for mistake in mistakes:
        category = mistake.get("category")

        if category and category not in focus_areas:
            focus_areas.append(category)

    if not focus_areas:
        focus_areas = ["previous journal corrections"]

    quest_data = {
        "target_language": target_language,
        "focus_areas": focus_areas[:3],
        "fill_blank": fill_blank,
        "spelling": {
            "items": spelling_items,
        },
        "matching": {
            "pairs": matching_pairs,
        },
    }

    return QuestResponse.model_validate(quest_data)