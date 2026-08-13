from models import FlashcardSet


def create_set(db_session, user_id, name="Test Set"):
    flashcard_set = FlashcardSet(
        user_id=user_id,
        name=name,
        language="German",
        source_type="manual",
        journal_entry_id=None,
    )

    db_session.add(flashcard_set)
    db_session.commit()
    db_session.refresh(flashcard_set)

    return flashcard_set


def test_owner_can_update_flashcard_set(
    client,
    db_session,
    test_user,
):
    flashcard_set = create_set(
        db_session,
        test_user["id"],
    )

    response = client.patch(
        f"/flashcard-sets/{flashcard_set.id}",
        json={
            "name": "Updated Set",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Set"


def test_non_owner_cannot_update_flashcard_set(
    client,
    db_session,
    other_user,
):
    flashcard_set = create_set(
        db_session,
        other_user["id"],
    )

    response = client.patch(
        f"/flashcard-sets/{flashcard_set.id}",
        json={
            "name": "Should Not Update",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Flashcard set not found"


def test_owner_can_delete_flashcard_set(
    client,
    db_session,
    test_user,
):
    flashcard_set = create_set(
        db_session,
        test_user["id"],
    )

    response = client.delete(
        f"/flashcard-sets/{flashcard_set.id}",
    )

    assert response.status_code == 204


def test_non_owner_cannot_delete_flashcard_set(
    client,
    db_session,
    other_user,
):
    flashcard_set = create_set(
        db_session,
        other_user["id"],
    )

    response = client.delete(
        f"/flashcard-sets/{flashcard_set.id}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Flashcard set not found"