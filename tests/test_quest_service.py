from models import JournalEntry
import pytest

from services.quest_service import (
    create_personalized_quests,
    get_quest_mistake_history,
    make_spot_mistake,
)


@pytest.mark.parametrize(
    "target_language,title,original,corrected",
    [
        (
            "German",
            "German Practice",
            "Ich bin gehen.",
            "Ich gehe.",
        ),
        (
            "French",
            "French Practice",
            "Je suis aller.",
            "Je suis allé.",
        ),
        (
            "Spanish",
            "Spanish Practice",
            "Yo soy cansado.",
            "Yo estoy cansado.",
        ),
    ],
)
def test_get_quest_mistake_history(
    db_session,
    test_user,
    target_language,
    title,
    original,
    corrected,
):
    entry = JournalEntry(
        user_id=test_user["id"],
        title=title,
        original_text=original,
        corrected_text=corrected,
        target_language=target_language,
        mistakes=[
            {
                "original": original,
                "corrected": corrected,
                "original_full": original,
                "corrected_full": corrected,
                "explanation": "Use the corrected form.",
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
    assert mistakes[0]["original"] == original
    assert mistakes[0]["corrected"] == corrected
    assert mistakes[0]["category"] == "grammar"
    assert mistakes[0]["target_language"] == target_language


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "target_language,"
        "original,"
        "corrected,"
        "original_full,"
        "corrected_full,"
        "spelling_original,"
        "spelling_corrected"
    ),
    [
        (
            "German",
            "bin gehen",
            "gehe",
            "Ich **bin gehen** nach Hause.",
            "Ich **gehe** nach Hause.",
            "gutte",
            "gute",
        ),
        (
            "French",
            "suis aller",
            "suis allé",
            "Je **suis aller** au magasin.",
            "Je **suis allé** au magasin.",
            "bonjor",
            "bonjour",
        ),
        (
            "Spanish",
            "soy cansado",
            "estoy cansado",
            "Yo **soy cansado** hoy.",
            "Yo **estoy cansado** hoy.",
            "grasias",
            "gracias",
        ),
    ],
)
async def test_create_personalized_quests(
    db_session,
    test_user,
    target_language,
    original,
    corrected,
    original_full,
    corrected_full,
    spelling_original,
    spelling_corrected,
):
    entry = JournalEntry(
        user_id=test_user["id"],
        title=f"{target_language} Practice",
        original_text=original_full.replace("**", ""),
        corrected_text=corrected_full.replace("**", ""),
        target_language=target_language,
        mistakes=[
            {
                "original": original,
                "corrected": corrected,
                "original_full": original_full,
                "corrected_full": corrected_full,
                "explanation": "Use the corrected form.",
                "category": "verb conjugation",
            },
            {
                "original": spelling_original,
                "corrected": spelling_corrected,
                "category": "spelling",
            },
        ],
    )

    db_session.add(entry)
    db_session.commit()

    result = await create_personalized_quests(
        user_id=test_user["id"],
        target_language=target_language,
        db=db_session,
    )

    assert result.target_language == target_language

    assert "verb conjugation" in result.focus_areas

    assert (
        result.spot_mistake.sentence
        == original_full.replace("**", "")
    )

    assert result.spot_mistake.incorrect == original
    assert result.spot_mistake.corrected == corrected

    assert (
        result.spot_mistake.corrected_sentence
        == corrected_full.replace("**", "")
    )

    assert result.spelling.items[0].word == spelling_corrected

    assert result.matching.pairs[0].prompt == original
    assert result.matching.pairs[0].match == corrected


@pytest.mark.parametrize(
    (
        "target_language,"
        "original,"
        "corrected,"
        "original_full,"
        "corrected_full"
    ),
    [
        (
            "German",
            "bin gehen",
            "gehe",
            "Ich **bin gehen** nach Hause.",
            "Ich **gehe** nach Hause.",
        ),
        (
            "French",
            "suis aller",
            "suis allé",
            "Je **suis aller** au magasin.",
            "Je **suis allé** au magasin.",
        ),
        (
            "Spanish",
            "soy cansado",
            "estoy cansado",
            "Yo **soy cansado** hoy.",
            "Yo **estoy cansado** hoy.",
        ),
    ],
)
def test_generate_quests_endpoint(
    client,
    db_session,
    test_user,
    target_language,
    original,
    corrected,
    original_full,
    corrected_full,
):
    entry = JournalEntry(
        user_id=test_user["id"],
        title=f"{target_language} Practice",
        original_text=original_full.replace("**", ""),
        corrected_text=corrected_full.replace("**", ""),
        target_language=target_language,
        mistakes=[
            {
                "original": original,
                "corrected": corrected,
                "original_full": original_full,
                "corrected_full": corrected_full,
                "explanation": "Use the corrected form.",
                "category": "verb conjugation",
            }
        ],
    )

    db_session.add(entry)
    db_session.commit()

    response = client.post(
        f"/quests/generate?target_language={target_language}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["target_language"] == target_language

    assert (
        data["spot_mistake"]["sentence"]
        == original_full.replace("**", "")
    )

    assert data["spot_mistake"]["incorrect"] == original
    assert data["spot_mistake"]["corrected"] == corrected

    assert (
        data["spot_mistake"]["corrected_sentence"]
        == corrected_full.replace("**", "")
    )

    assert data["matching"]["pairs"][0] == {
        "prompt": original,
        "match": corrected,
    }


@pytest.mark.parametrize(
    "target_language",
    [
        "German",
        "French",
        "Spanish",
        "Italian",
        "Portuguese",
        "Japanese",
    ],
)
def test_generate_quests_without_mistakes(
    client,
    target_language,
):
    response = client.post(
        f"/quests/generate?target_language={target_language}"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Not enough journal history to generate quests."
    }


def test_make_spot_mistake():
    mistake = {
        "original": "gehen",
        "corrected": "gehe",
        "original_full": "Ich **gehen** nach Hause.",
        "corrected_full": "Ich **gehe** nach Hause.",
        "explanation": "Use the conjugated first-person form.",
    }

    quest = make_spot_mistake(mistake)

    assert quest["sentence"] == "Ich gehen nach Hause."
    assert quest["incorrect"] == "gehen"
    assert quest["corrected"] == "gehe"
    assert quest["corrected_sentence"] == "Ich gehe nach Hause."
    assert quest["explanation"] == (
        "Use the conjugated first-person form."
    )