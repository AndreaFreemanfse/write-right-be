from models import JournalEntry, UserActivity
import routes.journal as journal_route


def create_journal_entry(
    db_session,
    user_id,
    title="Test Journal",
    original_text="Ich fare einen Lastwagen.",
):
    entry = JournalEntry(
        user_id=user_id,
        title=title,
        original_text=original_text,
        corrected_text="Ich fahre einen Lastwagen.",
        mistakes=[],
        target_language="German",
    )

    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    return entry


async def fake_correct_text(
    text,
    native_language,
    target_language,
):
    return {
        "text": "Ich fahre einen Lastwagen.",
        "mistakes": [
            {
                "original": "fare",
                "corrected": "fahre",
                "original_full": "Ich fare einen Lastwagen.",
                "corrected_full": "Ich fahre einen Lastwagen.",
                "explanation": "The verb should be 'fahre'.",
                "category": "verb_conjugation",
            }
        ],
        "accuracy": {
            "score": 90,
            "summary": "Good work.",
            "categories": {
                "grammar": 90,
                "vocabulary": 100,
                "spelling": 90,
                "sentenceStructure": 100,
            },
            "improvementNote": "Review verb conjugation.",
        },
    }


def test_analyze_journal_persists_entry(
    client,
    db_session,
    test_user,
    monkeypatch,
):
    monkeypatch.setattr(
        journal_route,
        "correct_text",
        fake_correct_text,
    )

    response = client.post(
        "/journal/analyze",
        json={
            "title": "Truck Journal",
            "text": "Ich fare einen Lastwagen.",
            "native_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["title"] == "Truck Journal"
    assert result["text"] == "Ich fahre einen Lastwagen."
    assert result["journal_entry_id"] is not None

    entry = (
        db_session.query(JournalEntry)
        .filter(
            JournalEntry.id == result["journal_entry_id"]
        )
        .first()
    )

    assert entry is not None
    assert entry.user_id == test_user["id"]
    assert entry.title == "Truck Journal"
    assert entry.original_text == "Ich fare einen Lastwagen."
    assert entry.corrected_text == "Ich fahre einen Lastwagen."
    assert entry.target_language == "German"

    assert len(entry.mistakes) == 1
    assert entry.mistakes[0]["start"] == 4
    assert entry.mistakes[0]["end"] == 8


def test_analyze_journal_records_activity(
    client,
    db_session,
    test_user,
    monkeypatch,
):
    monkeypatch.setattr(
        journal_route,
        "correct_text",
        fake_correct_text,
    )

    response = client.post(
        "/journal/analyze",
        json={
            "title": "Activity Test",
            "text": "Ich fare einen Lastwagen.",
            "native_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 200

    activity = (
        db_session.query(UserActivity)
        .filter(
            UserActivity.user_id == test_user["id"],
            UserActivity.activity_type == "journal_analyzed",
        )
        .first()
    )

    assert activity is not None
    assert activity.activity_data["accuracy_score"] == 90
    assert activity.activity_data["target_language"] == "German"


def test_user_only_gets_own_journal_entries(
    client,
    db_session,
    test_user,
    other_user,
):
    create_journal_entry(
        db_session,
        test_user["id"],
        title="My Journal",
    )

    create_journal_entry(
        db_session,
        other_user["id"],
        title="Other User Journal",
    )

    response = client.get("/journal/entries")

    assert response.status_code == 200

    entries = response.json()

    assert len(entries) == 1
    assert entries[0]["title"] == "My Journal"


def test_owner_can_delete_journal_entry(
    client,
    db_session,
    test_user,
):
    entry = create_journal_entry(
        db_session,
        test_user["id"],
    )

    response = client.delete(
        f"/journal/{entry.id}",
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Journal entry deleted successfully"
    }

    deleted_entry = (
        db_session.query(JournalEntry)
        .filter(JournalEntry.id == entry.id)
        .first()
    )

    assert deleted_entry is None


def test_non_owner_cannot_delete_journal_entry(
    client,
    db_session,
    other_user,
):
    entry = create_journal_entry(
        db_session,
        other_user["id"],
    )

    response = client.delete(
        f"/journal/{entry.id}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Journal entry not found"

def test_lifetime_journal_count_does_not_decrease_when_entry_is_deleted(
    client,
    db_session,
    test_user,
):
    first_entry = create_journal_entry(
        db_session,
        test_user["id"],
        title="First Journal",
    )

    create_journal_entry(
        db_session,
        test_user["id"],
        title="Second Journal",
    )

    db_session.add_all(
        [
            UserActivity(
                user_id=test_user["id"],
                activity_type="journal_analyzed",
                activity_data={},
            ),
            UserActivity(
                user_id=test_user["id"],
                activity_type="journal_analyzed",
                activity_data={},
            ),
        ]
    )
    db_session.commit()

    delete_response = client.delete(
        f"/journal/{first_entry.id}",
    )

    assert delete_response.status_code == 200

    stats_response = client.get("/journal/stats")

    assert stats_response.status_code == 200
    assert stats_response.json()["lifetime_journal_count"] == 2