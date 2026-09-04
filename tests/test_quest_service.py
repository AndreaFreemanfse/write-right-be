from models import JournalEntry
import pytest
from services.quest_service import (
    create_personalized_quests,
    get_quest_mistake_history,
    make_fill_blank,
)


def test_get_quest_mistake_history(db_session, test_user):
    entry = JournalEntry(
        user_id=test_user["id"],
        title="German Practice",
        original_text="Ich bin gehen.",
        corrected_text="Ich gehe.",
        target_language="German",
        mistakes=[
            {
                "original": "bin gehen",
                "corrected": "gehe",
                "original_full": "Ich bin gehen.",
                "corrected_full": "Ich gehe.",
                "explanation": "Use the conjugated verb directly.",
                "category": "grammar",
            }
        ],
    )

    db_session.add(entry)
    db_session.commit()

    mistakes = get_quest_mistake_history(
        user_id=test_user["id"],
        db=db_session,
    )

    assert len(mistakes) == 1
    assert mistakes[0]["original"] == "bin gehen"
    assert mistakes[0]["corrected"] == "gehe"
    assert mistakes[0]["category"] == "grammar"
    assert mistakes[0]["target_language"] == "German"


@pytest.mark.anyio
async def test_create_personalized_quests(db_session, test_user):
    entry = JournalEntry(
        user_id=test_user["id"],
        title="German Practice",
        original_text="Ich bin gehen.",
        corrected_text="Ich gehe.",
        target_language="German",
        mistakes=[
            {
                "original": "bin gehen",
                "corrected": "gehe",
                "original_full": "Ich **bin gehen** nach Hause.",
                "corrected_full": "Ich **gehe** nach Hause.",
                "explanation": "Use the conjugated verb directly.",
                "category": "verb conjugation",
            },
            {
                "original": "gutte",
                "corrected": "gute",
                "category": "spelling",
            },
        ],
    )

    db_session.add(entry)
    db_session.commit()

    result = await create_personalized_quests(
        user_id=test_user["id"],
        db=db_session,
    )

    assert result.target_language == "German"
    assert "verb conjugation" in result.focus_areas

    assert result.fill_blank.sentence == "Ich ___ nach Hause."
    assert result.fill_blank.answer == "gehe"

    assert result.spelling.items[0].word == "gute"

    assert result.matching.pairs[0].prompt == "bin gehen"
    assert result.matching.pairs[0].match == "gehe"


def test_generate_quests_endpoint(client, db_session, test_user):
    entry = JournalEntry(
        user_id=test_user["id"],
        title="German Practice",
        original_text="Ich bin gehen.",
        corrected_text="Ich gehe.",
        target_language="German",
        mistakes=[
            {
                "original": "bin gehen",
                "corrected": "gehe",
                "original_full": "Ich **bin gehen** nach Hause.",
                "corrected_full": "Ich **gehe** nach Hause.",
                "explanation": "Use the conjugated verb directly.",
                "category": "verb conjugation",
            }
        ],
    )

    db_session.add(entry)
    db_session.commit()

    response = client.post("/quests/generate")

    assert response.status_code == 200

    data = response.json()

    assert data["target_language"] == "German"
    assert data["fill_blank"]["sentence"] == "Ich ___ nach Hause."
    assert data["fill_blank"]["answer"] == "gehe"

    assert data["matching"]["pairs"][0] == {
        "prompt": "bin gehen",
        "match": "gehe",
    }

def test_generate_quests_without_mistakes(client):
    response = client.post("/quests/generate")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Not enough journal history to generate quests."
    }


def test_make_fill_blank():
    mistake = {
        "original": "gehen",
        "corrected": "gehe",
        "corrected_full": "Ich **gehe** nach Hause.",
        "explanation": "Use the conjugated first-person form.",
    }

    quest = make_fill_blank(mistake)

    assert quest["sentence"] == "Ich ___ nach Hause."
    assert quest["answer"] == "gehe"
    assert quest["explanation"] == (
        "Use the conjugated first-person form."
    )