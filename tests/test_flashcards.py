from models import Flashcard, FlashcardSet


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


def create_card(
    db_session,
    user_id,
    set_id,
    front="Hallo",
    back="Hello",
):
    flashcard = Flashcard(
        user_id=user_id,
        set_id=set_id,
        front=front,
        back=back,
        language="German",
    )

    db_session.add(flashcard)
    db_session.commit()
    db_session.refresh(flashcard)

    return flashcard


def test_owner_can_create_flashcard(
    client,
    db_session,
    test_user,
):
    flashcard_set = create_set(
        db_session,
        test_user["id"],
    )

    response = client.post(
        "/flashcards",
        json={
            "set_id": flashcard_set.id,
            "front": "Ich fahre",
            "back": "I drive",
            "language": "German",
        },
    )

    assert response.status_code == 201
    assert response.json()["front"] == "Ich fahre"
    assert response.json()["back"] == "I drive"


def test_non_owner_cannot_create_flashcard(
    client,
    db_session,
    other_user,
):
    flashcard_set = create_set(
        db_session,
        other_user["id"],
    )

    response = client.post(
        "/flashcards",
        json={
            "set_id": flashcard_set.id,
            "front": "Nicht erlaubt",
            "back": "Not allowed",
            "language": "German",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Flashcard set not found"


def test_user_only_gets_own_flashcards(
    client,
    db_session,
    test_user,
    other_user,
):
    own_set = create_set(
        db_session,
        test_user["id"],
        name="Own Set",
    )

    other_set = create_set(
        db_session,
        other_user["id"],
        name="Other Set",
    )

    create_card(
        db_session,
        test_user["id"],
        own_set.id,
        front="Own Card",
    )

    create_card(
        db_session,
        other_user["id"],
        other_set.id,
        front="Other Card",
    )

    response = client.get("/flashcards")

    assert response.status_code == 200

    cards = response.json()

    assert len(cards) == 1
    assert cards[0]["front"] == "Own Card"


def test_owner_can_update_flashcard(
    client,
    db_session,
    test_user,
):
    flashcard_set = create_set(
        db_session,
        test_user["id"],
    )

    flashcard = create_card(
        db_session,
        test_user["id"],
        flashcard_set.id,
    )

    response = client.patch(
        f"/flashcards/{flashcard.id}",
        json={
            "front": "Updated Front",
            "mastered": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["front"] == "Updated Front"
    assert response.json()["mastered"] is True


def test_non_owner_cannot_update_flashcard(
    client,
    db_session,
    other_user,
):
    flashcard_set = create_set(
        db_session,
        other_user["id"],
    )

    flashcard = create_card(
        db_session,
        other_user["id"],
        flashcard_set.id,
    )

    response = client.patch(
        f"/flashcards/{flashcard.id}",
        json={
            "front": "Should Not Update",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Flashcard not found"


def test_owner_can_delete_flashcard(
    client,
    db_session,
    test_user,
):
    flashcard_set = create_set(
        db_session,
        test_user["id"],
    )

    flashcard = create_card(
        db_session,
        test_user["id"],
        flashcard_set.id,
    )

    response = client.delete(
        f"/flashcards/{flashcard.id}",
    )

    assert response.status_code == 204


def test_non_owner_cannot_delete_flashcard(
    client,
    db_session,
    other_user,
):
    flashcard_set = create_set(
        db_session,
        other_user["id"],
    )

    flashcard = create_card(
        db_session,
        other_user["id"],
        flashcard_set.id,
    )

    response = client.delete(
        f"/flashcards/{flashcard.id}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Flashcard not found"