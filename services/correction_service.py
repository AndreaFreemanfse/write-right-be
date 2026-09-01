from services.ai_service import ai_correct_text

from services.providers import languagetool_provider
from services.providers import japanese_provider
from services.providers import korean_provider
from services.providers import chinese_provider


# ------------------------------------------------------------------
# Providers
# ------------------------------------------------------------------

PROVIDERS = {
    "languagetool": languagetool_provider,
    "japanese_provider": japanese_provider,
    "korean_provider": korean_provider,
    "chinese_provider": chinese_provider,
}


CORRECTION_PROVIDERS = {
    "English": "languagetool",
    "Spanish": "languagetool",
    "French": "languagetool",
    "German": "languagetool",
    "Japanese": "japanese_provider",
    "Korean": "korean_provider",
    "Chinese": "chinese_provider",
}


DEFAULT_PROVIDER = "languagetool"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def find_occurrence(text, substring, start_position=0):
    if not substring:
        return -1

    return text.find(substring, start_position)


def add_indices(original_text, analysis):
    """
    Add start/end positions to each mistake.

    Positions always refer to the ORIGINAL text.
    """

    if not isinstance(analysis, dict):
        return analysis

    mistakes = analysis.get("mistakes", [])

    if not isinstance(mistakes, list):
        analysis["mistakes"] = []
        return analysis

    last_index = 0

    for mistake in mistakes:
        if not isinstance(mistake, dict):
            continue

        original = mistake.get("original", "")

        if not original:
            mistake["start"] = None
            mistake["end"] = None
            continue

        # If the provider already supplied valid indices,
        # preserve them.
        start = mistake.get("start")
        end = mistake.get("end")

        if (
            isinstance(start, int)
            and isinstance(end, int)
            and start >= 0
            and end > start
            and end <= len(original_text)
            and original_text[start:end] == original
        ):
            last_index = end
            continue

        start = find_occurrence(
            original_text,
            original,
            last_index,
        )

        if start == -1:
            mistake["start"] = None
            mistake["end"] = None
            continue

        mistake["start"] = start
        mistake["end"] = start + len(original)

        last_index = mistake["end"]

    return analysis


def empty_accuracy():
    return {
        "score": 100,
        "summary": "No significant corrections were found.",
        "categories": {
            "grammar": 100,
            "vocabulary": 100,
            "spelling": 100,
            "sentenceStructure": 100,
        },
        "improvementNote": "",
    }


def ensure_accuracy(analysis):
    """
    Guarantee that every analysis has the accuracy structure
    required by the API response schema.
    """

    if not isinstance(analysis, dict):
        analysis = {}

    accuracy = analysis.get("accuracy")

    if not isinstance(accuracy, dict):
        analysis["accuracy"] = empty_accuracy()
        return analysis

    accuracy.setdefault("score", 100)
    accuracy.setdefault(
        "summary",
        "No significant corrections were found.",
    )
    accuracy.setdefault(
        "categories",
        {
            "grammar": 100,
            "vocabulary": 100,
            "spelling": 100,
            "sentenceStructure": 100,
        },
    )
    accuracy.setdefault("improvementNote", "")

    categories = accuracy["categories"]

    if not isinstance(categories, dict):
        accuracy["categories"] = {
            "grammar": 100,
            "vocabulary": 100,
            "spelling": 100,
            "sentenceStructure": 100,
        }

    return analysis


# ------------------------------------------------------------------
# LanguageTool
# ------------------------------------------------------------------

def build_language_tool_analysis(text, matches):
    mistakes = []

    corrected_text = text

    for match in matches:
        if not match.replacements:
            continue

        start = match.offset
        end = start + match.error_length

        if start < 0 or end > len(text):
            continue

        original = text[start:end]
        corrected = match.replacements[0]

        if not original or not corrected:
            continue

        corrected_full = (
            text[:start]
            + corrected
            + text[end:]
        )

        original_full = (
            text[:start]
            + f"**{original}**"
            + text[end:]
        )

        corrected_full = (
            corrected_full[:start]
            + f"**{corrected}**"
            + corrected_full[start + len(corrected):]
        )

        mistakes.append(
            {
                "original": original,
                "corrected": corrected,
                "original_full": original_full,
                "corrected_full": corrected_full,
                "explanation": None,
                "category": getattr(
                    match,
                    "category",
                    None,
                ),
                "loading": False,
                "start": start,
                "end": end,
            }
        )

    # Apply corrections from right to left.
    for match in sorted(
        matches,
        key=lambda item: item.offset,
        reverse=True,
    ):
        if not match.replacements:
            continue

        start = match.offset
        end = start + match.error_length

        if start < 0 or end > len(corrected_text):
            continue

        corrected_text = (
            corrected_text[:start]
            + match.replacements[0]
            + corrected_text[end:]
        )

    return {
        "text": corrected_text,
        "mistakes": mistakes,
        "accuracy": empty_accuracy(),
    }


# ------------------------------------------------------------------
# Provider handling
# ------------------------------------------------------------------

def run_provider(
    text,
    target_language,
    provider_name,
):
    provider = PROVIDERS.get(provider_name)

    if provider is None:
        print(
            f"Provider '{provider_name}' is unavailable."
        )
        return {
            "text": text,
            "mistakes": [],
            "accuracy": empty_accuracy(),
        }

    print(
        f"Checking {target_language} "
        f"with {provider_name}..."
    )

    try:
        matches = provider.check(
            text,
            target_language,
        )
    except Exception as error:
        print(
            f"Provider '{provider_name}' failed: "
            f"{error}"
        )

        return {
            "text": text,
            "mistakes": [],
            "accuracy": empty_accuracy(),
        }

    if not matches:
        print(
            f"{provider_name} found no corrections."
        )

        return {
            "text": text,
            "mistakes": [],
            "accuracy": empty_accuracy(),
        }

    print(
        f"{provider_name} found "
        f"{len(matches)} correction(s)."
    )

    # LanguageTool returns Match objects.
    if provider_name == "languagetool":
        return build_language_tool_analysis(
            text,
            matches,
        )

    # Specialized providers may already return
    # WriteRight-compatible analysis.
    if isinstance(matches, dict):
        analysis = matches
        ensure_accuracy(analysis)
        return analysis

    return {
        "text": text,
        "mistakes": [],
        "accuracy": empty_accuracy(),
    }


# ------------------------------------------------------------------
# Main correction function
# ------------------------------------------------------------------

async def correct_text(
    text,
    native_language="English",
    target_language="English",
    review_depth="quick",
):
    """
    Quick:
        Provider only.

    In-depth:
        Provider + AI.

    Quick is intentionally the fastest path.
    """

    if text is None:
        text = ""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return {
            "text": "",
            "mistakes": [],
            "accuracy": empty_accuracy(),
            "original_text": "",
        }

    if review_depth not in {"quick", "in-depth"}:
        review_depth = "quick"

    print(f"Review mode: {review_depth}")

    provider_name = CORRECTION_PROVIDERS.get(
        target_language,
        DEFAULT_PROVIDER,
    )

    # --------------------------------------------------------------
    # QUICK
    # --------------------------------------------------------------

    if review_depth == "quick":
        analysis = run_provider(
            text,
            target_language,
            provider_name,
        )

        analysis = add_indices(
            text,
            analysis,
        )

        ensure_accuracy(analysis)

        analysis["original_text"] = text

        return analysis

    # --------------------------------------------------------------
    # IN-DEPTH
    # --------------------------------------------------------------

    provider_analysis = run_provider(
        text,
        target_language,
        provider_name,
    )

    provider_analysis = add_indices(
        text,
        provider_analysis,
    )

    provider_mistakes = provider_analysis.get(
        "mistakes",
        [],
    )

    print("Running AI in-depth review...")

    try:
        ai_analysis = await ai_correct_text(
            text,
            native_language,
            target_language,
        )
    except Exception as error:
        print(
            f"AI correction failed: {error}"
        )

        ai_analysis = {
            "text": text,
            "mistakes": [],
            "accuracy": provider_analysis.get(
                "accuracy",
                empty_accuracy(),
            ),
        }

    ai_analysis = add_indices(
        text,
        ai_analysis,
    )

    ai_mistakes = ai_analysis.get(
        "mistakes",
        [],
    )

    print(
        f"AI found {len(ai_mistakes)} correction(s)."
    )

    # --------------------------------------------------------------
    # Merge
    #
    # For in-depth mode, AI corrections take priority when
    # they overlap a provider correction.
    # --------------------------------------------------------------

    merged_mistakes = []

    for provider_mistake in provider_mistakes:
        merged_mistakes.append(
            provider_mistake
        )

    for ai_mistake in ai_mistakes:
        ai_start = ai_mistake.get("start")
        ai_end = ai_mistake.get("end")

        if not isinstance(ai_start, int):
            continue

        if not isinstance(ai_end, int):
            continue

        # Remove provider corrections that overlap
        # the AI correction.
        merged_mistakes = [
            mistake
            for mistake in merged_mistakes
            if not (
                isinstance(mistake.get("start"), int)
                and isinstance(mistake.get("end"), int)
                and mistake["start"] < ai_end
                and mistake["end"] > ai_start
            )
        ]

        merged_mistakes.append(ai_mistake)

    # Remove duplicates.
    unique = []
    seen = set()

    for mistake in merged_mistakes:
        key = (
            mistake.get("start"),
            mistake.get("end"),
            mistake.get("original"),
            mistake.get("corrected"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(mistake)

    unique.sort(
        key=lambda mistake: (
            mistake.get("start", -1),
            mistake.get("end", -1),
        )
    )

    # --------------------------------------------------------------
    # Apply corrections to ORIGINAL text
    # --------------------------------------------------------------

    corrected_text = text

    valid_mistakes = []

    for mistake in unique:
        start = mistake.get("start")
        end = mistake.get("end")
        original = mistake.get("original")
        corrected = mistake.get("corrected")

        if not isinstance(start, int):
            continue

        if not isinstance(end, int):
            continue

        if not original:
            continue

        if corrected is None:
            continue

        if start < 0 or end <= start:
            continue

        if end > len(text):
            continue

        if text[start:end] != original:
            continue

        valid_mistakes.append(mistake)

    for mistake in sorted(
        valid_mistakes,
        key=lambda item: item["start"],
        reverse=True,
    ):
        start = mistake["start"]
        end = mistake["end"]

        corrected_text = (
            corrected_text[:start]
            + mistake["corrected"]
            + corrected_text[end:]
        )

    # AI accuracy is more useful for in-depth mode.
    accuracy = ai_analysis.get(
        "accuracy",
        provider_analysis.get(
            "accuracy",
            empty_accuracy(),
        ),
    )

    return {
        "text": corrected_text,
        "mistakes": valid_mistakes,
        "accuracy": accuracy,
        "original_text": text,
    }

