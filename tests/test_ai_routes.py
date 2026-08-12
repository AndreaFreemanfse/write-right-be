import routes.explanation as explanation_route
import routes.translate as translate_route


async def fake_translate_word(
    text,
    source_language,
    target_language,
):
    return {
        "translation": "Lastwagen",
        "source_language": source_language,
        "target_language": target_language,
    }


async def fake_generate_explanation(
    original,
    corrected,
    native_language,
    target_language,
):
    return {
        "explanation": "Use the correct verb form.",
        "category": "verb_conjugation",
    }


async def fake_value_error(*args, **kwargs):
    raise ValueError("AI service returned invalid data.")


async def fake_unexpected_error(*args, **kwargs):
    raise RuntimeError("Unexpected failure")


def test_translate_returns_mocked_translation(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        translate_route,
        "translate_word",
        fake_translate_word,
    )

    response = client.post(
        "/translate",
        json={
            "text": "truck",
            "source_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 200
    assert response.json()["translation"] == "Lastwagen"


def test_translate_value_error_returns_502(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        translate_route,
        "translate_word",
        fake_value_error,
    )

    response = client.post(
        "/translate",
        json={
            "text": "truck",
            "source_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI service returned invalid data."
    )


def test_translate_unexpected_error_returns_500(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        translate_route,
        "translate_word",
        fake_unexpected_error,
    )

    response = client.post(
        "/translate",
        json={
            "text": "truck",
            "source_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The translation could not be completed."
    )


def test_explanation_returns_mocked_response(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        explanation_route,
        "generate_explanation",
        fake_generate_explanation,
    )

    response = client.post(
        "/explanation",
        json={
            "original": "Ich fare",
            "corrected": "Ich fahre",
            "native_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "Use the correct verb form.",
        "category": "verb_conjugation",
    }


def test_explanation_value_error_returns_502(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        explanation_route,
        "generate_explanation",
        fake_value_error,
    )

    response = client.post(
        "/explanation",
        json={
            "original": "Ich fare",
            "corrected": "Ich fahre",
            "native_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI service returned invalid data."
    )


def test_explanation_unexpected_error_returns_500(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        explanation_route,
        "generate_explanation",
        fake_unexpected_error,
    )

    response = client.post(
        "/explanation",
        json={
            "original": "Ich fare",
            "corrected": "Ich fahre",
            "native_language": "English",
            "target_language": "German",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The explanation generation could not be completed."
    )