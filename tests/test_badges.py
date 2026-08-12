from models import Badge, JournalEntry, UserActivity, UserBadge, Flashcard, FlashcardSet

from badge_service import (
    award_badge,
    evaluate_progress_badges,
    seed_badges,
)


def create_journal_entry(
    db_session,
    user_id,
    title="Test Journal",
):
    entry = JournalEntry(
        user_id=user_id,
        title=title,
        original_text="Ich fahre einen Lastwagen.",
        corrected_text="Ich fahre einen Lastwagen.",
        mistakes=[],
        target_language="German",
    )

    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    return entry


def create_journal_activity(
    db_session,
    user_id,
    accuracy_score,
):
    activity = UserActivity(
        user_id=user_id,
        activity_type="journal_analyzed",
        activity_data={
            "accuracy_score": accuracy_score,
            "target_language": "German",
        },
    )

    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    return activity


def test_seed_badges_creates_badge_definitions(
    db_session,
):
    seed_badges(db_session)

    badges = db_session.query(Badge).all()

    assert len(badges) == 11


def test_first_journal_awards_first_steps(
    db_session,
    test_user,
):
    create_journal_entry(
        db_session,
        test_user["id"],
    )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "first_steps" in badge_keys


def test_high_accuracy_awards_high_accuracy_badge(
    db_session,
    test_user,
):
    create_journal_activity(
        db_session,
        test_user["id"],
        accuracy_score=90,
    )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "high_accuracy" in badge_keys


def test_perfect_accuracy_awards_perfect_journal(
    db_session,
    test_user,
):
    create_journal_activity(
        db_session,
        test_user["id"],
        accuracy_score=100,
    )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "high_accuracy" in badge_keys
    assert "perfect_journal" in badge_keys


def test_badge_is_not_awarded_twice(
    db_session,
    test_user,
):
    seed_badges(db_session)

    first_award = award_badge(
        user_id=test_user["id"],
        badge_key="first_steps",
        db=db_session,
    )

    second_award = award_badge(
        user_id=test_user["id"],
        badge_key="first_steps",
        db=db_session,
    )

    assert first_award is not None
    assert second_award is None

    badge = (
        db_session.query(Badge)
        .filter(Badge.key == "first_steps")
        .first()
    )

    user_badges = (
        db_session.query(UserBadge)
        .filter(
            UserBadge.user_id == test_user["id"],
            UserBadge.badge_id == badge.id,
        )
        .all()
    )

    assert len(user_badges) == 1


def test_badge_endpoint_only_returns_current_users_badges(
    client,
    db_session,
    test_user,
    other_user,
):
    seed_badges(db_session)

    award_badge(
        user_id=test_user["id"],
        badge_key="first_steps",
        db=db_session,
    )

    award_badge(
        user_id=other_user["id"],
        badge_key="journal_explorer",
        db=db_session,
    )

    response = client.get("/badges")

    assert response.status_code == 200

    badges = response.json()

    assert len(badges) == 1
    assert badges[0]["badge"]["key"] == "first_steps"

def create_flashcard_set(
    db_session,
    user_id,
    name,
):
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


def create_flashcard(
    db_session,
    user_id,
    set_id,
    front,
    mastered=False,
):
    flashcard = Flashcard(
        user_id=user_id,
        set_id=set_id,
        front=front,
        back=f"Answer {front}",
        language="German",
        mastered=mastered,
    )

    db_session.add(flashcard)
    return flashcard


def test_five_journals_award_journal_explorer(
    db_session,
    test_user,
):
    for index in range(5):
        create_journal_entry(
            db_session,
            test_user["id"],
            title=f"Journal {index}",
        )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "journal_explorer" in badge_keys


def test_first_flashcard_set_awards_vault_starter(
    db_session,
    test_user,
):
    create_flashcard_set(
        db_session,
        test_user["id"],
        "First Set",
    )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "vault_starter" in badge_keys


def test_six_flashcard_sets_award_vault_builder(
    db_session,
    test_user,
):
    for index in range(6):
        create_flashcard_set(
            db_session,
            test_user["id"],
            f"Set {index}",
        )

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "vault_builder" in badge_keys


def test_twenty_five_flashcards_award_card_collector(
    db_session,
    test_user,
):
    flashcard_set = create_flashcard_set(
        db_session,
        test_user["id"],
        "Collector Set",
    )

    for index in range(25):
        create_flashcard(
            db_session,
            test_user["id"],
            flashcard_set.id,
            front=f"Card {index}",
        )

    db_session.commit()

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "card_collector" in badge_keys


def test_ten_mastered_flashcards_award_study_habit(
    db_session,
    test_user,
):
    flashcard_set = create_flashcard_set(
        db_session,
        test_user["id"],
        "Study Set",
    )

    for index in range(10):
        create_flashcard(
            db_session,
            test_user["id"],
            flashcard_set.id,
            front=f"Mastered {index}",
            mastered=True,
        )

    db_session.commit()

    newly_earned = evaluate_progress_badges(
        user_id=test_user["id"],
        db=db_session,
    )

    badge_keys = [
        user_badge.badge.key
        for user_badge in newly_earned
    ]

    assert "study_habit" in badge_keys