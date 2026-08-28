from models import JournalEntry
from services.quest_service import (
    get_quest_mistake_history
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

import pytest
from unittest.mock import AsyncMock, patch


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
                "category": "grammar",
            }
        ],
    )

    db_session.add(entry)
    db_session.commit()

    mock_quest_data = {
        "target_language": "German",
        "focus_areas": ["verb conjugation"],
        "fill_blank": {
            "sentence": "Ich ___ jeden Tag Deutsch.",
            "answer": "lerne",
            "hint": "Conjugate lernen for ich.",
            "explanation": "The first-person form is lerne.",
        },
        "spelling": {
            "items": [
                {"word": "schreiben", "clue": "To write"},
                {"word": "lernen", "clue": "To learn"},
                {"word": "sprechen", "clue": "To speak"},
            ]
        },
        "matching": {
            "pairs": [
                {"prompt": "ich", "match": "gehe"},
                {"prompt": "du", "match": "gehst"},
                {"prompt": "wir", "match": "gehen"},
                {"prompt": "er", "match": "geht"},
            ]
        },
    }

    with patch(
        "services.quest_service.generate_quests",
        new_callable=AsyncMock,
        return_value=mock_quest_data,
    ) as mock_generate:
        from services.quest_service import create_personalized_quests

        result = await create_personalized_quests(
            user_id=test_user["id"],
            db=db_session,
        )

    assert result.target_language == "German"
    assert result.focus_areas == ["verb conjugation"]
    assert result.fill_blank.answer == "lerne"
    assert len(result.spelling.items) == 3
    assert len(result.matching.pairs) == 4

    mock_generate.assert_awaited_once()


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
                "category": "grammar",
            }
        ],
    )

    db_session.add(entry)
    db_session.commit()

    mock_quest_data = {
        "target_language": "German",
        "focus_areas": ["verb conjugation"],
        "fill_blank": {
            "sentence": "Ich ___ jeden Tag Deutsch.",
            "answer": "lerne",
            "hint": "Conjugate lernen for ich.",
            "explanation": "The first-person form is lerne.",
        },
        "spelling": {
            "items": [
                {"word": "schreiben", "clue": "To write"},
                {"word": "lernen", "clue": "To learn"},
                {"word": "sprechen", "clue": "To speak"},
            ]
        },
        "matching": {
            "pairs": [
                {"prompt": "ich", "match": "gehe"},
                {"prompt": "du", "match": "gehst"},
                {"prompt": "wir", "match": "gehen"},
                {"prompt": "er", "match": "geht"},
            ]
        },
    }

    with patch(
        "services.quest_service.generate_quests",
        new_callable=AsyncMock,
        return_value=mock_quest_data,
    ):
        response = client.post("/quests/generate")

    assert response.status_code == 200

    data = response.json()

    assert data["target_language"] == "German"
    assert data["focus_areas"] == ["verb conjugation"]
    assert data["fill_blank"]["answer"] == "lerne"
    assert len(data["spelling"]["items"]) == 3
    assert len(data["matching"]["pairs"]) == 4

def test_generate_quests_without_mistakes(client):
    response = client.post("/quests/generate")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Not enough journal history to generate quests."
    }