from services.ai_service import ai_correct_text

from services.providers import languagetool_provider
from services.providers import japanese_provider
from services.providers import korean_provider
from services.providers import chinese_provider


# This file decides which correction tool should be used.

# Available correction providers.
# Add new providers here as we introduce them.
PROVIDERS = {
    "languagetool": languagetool_provider,
    "japanese_provider": japanese_provider,
    "korean_provider": korean_provider,
    "chinese_provider": chinese_provider,
}


# Which provider should be used for each target language.
#
# LanguageTool currently handles:
# English, Spanish, French, and German.
#
# Japanese, Korean, and Chinese have their own provider slots
# so we can add specialized grammar engines later.
CORRECTION_PROVIDERS = {
    "English": "languagetool",
    "Spanish": "languagetool",
    "French": "languagetool",
    "German": "languagetool",
    "Japanese": "japanese_provider",
    "Korean": "korean_provider",
    "Chinese": "chinese_provider",
}


# Fallback provider for languages not explicitly configured above.
DEFAULT_PROVIDER = "languagetool"


# Find the occurrence of a substring in a string.
# Used to find the start index of each mistake in the original text.
def find_occurrence(text, substring, start_position=0):
    return text.find(substring, start_position)


# Add start/end indices to each mistake for frontend highlighting.
def add_indices(original_text, analysis):
    last_index = 0

    for mistake in analysis["mistakes"]:
        start = find_occurrence(
            original_text,
            mistake["original"],
            last_index
        )

        if start != -1:
            mistake["start"] = start
            mistake["end"] = start + len(mistake["original"])
            last_index = mistake["end"]
        else:
            mistake["start"] = None
            mistake["end"] = None

    return analysis


# Convert LanguageTool matches into the format expected by WriteRight.
def build_language_tool_analysis(text, matches):
    mistakes = []

    for match in matches:
        if not match.replacements:
            continue

        original = text[
            match.offset:
            match.offset + match.error_length
        ]

        corrected = match.replacements[0]

        # Build the complete corrected version of the text
        # with this particular correction applied.
        corrected_text = (
            text[:match.offset]
            + corrected
            + text[match.offset + match.error_length:]
        )

        # Highlight the original mistake.
        original_full = (
            text[:match.offset]
            + f"**{original}**"
            + text[match.offset + match.error_length:]
        )

        # Highlight the corrected version.
        corrected_full = (
            corrected_text[:match.offset]
            + f"**{corrected}**"
            + corrected_text[
                match.offset + len(corrected):
            ]
        )

        mistakes.append({
            "original": original,
            "corrected": corrected,
            "original_full": original_full,
            "corrected_full": corrected_full,
            "explanation": None,
            "category": match.category,
            "loading": False,
        })

    # Apply corrections from right to left so that the original
    # LanguageTool offsets remain valid while modifying the text.
    corrected_text = text

    for match in sorted(
        matches,
        key=lambda m: m.offset,
        reverse=True
    ):
        if not match.replacements:
            continue

        corrected_text = (
            corrected_text[:match.offset]
            + match.replacements[0]
            + corrected_text[
                match.offset + match.error_length:
            ]
        )

    return {
        "text": corrected_text,
        "mistakes": mistakes,
    }


async def correct_text(
    text,
    native_language="English",
    target_language="English",
):
    """
    Main correction entry point for WriteRight.

    The function:

    1. Selects the appropriate correction provider.
    2. Runs the provider against the user's text.
    3. Converts provider results into WriteRight's format.
    4. Falls back to AI if the provider finds no corrections.
    """

    # Determine which provider should handle this language.
    provider_name = CORRECTION_PROVIDERS.get(
        target_language,
        DEFAULT_PROVIDER
    )

    # Get the provider from the registry.
    provider = PROVIDERS.get(provider_name)

    # Safety check in case a provider is configured but hasn't
    # actually been added to PROVIDERS.
    if provider is None:
        print(
            f"Provider '{provider_name}' is not available. "
            "Falling back to AI."
        )

        return await ai_correct_text(
            text,
            native_language,
            target_language,
        )

    print(
        f"Checking {target_language} with {provider_name}..."
    )

    # Run the selected correction provider.
    matches = provider.check(
        text,
        target_language
    )

    # If the provider found corrections, convert them into
    # WriteRight's standard analysis format.
    if matches:
        print(
            f"{provider_name} found "
            f"{len(matches)} correction(s)."
        )

        analysis = build_language_tool_analysis(
            text,
            matches
        )

        # Add character positions for frontend highlighting.
        analysis = add_indices(
            text,
            analysis
        )

        return analysis

    # The correction provider did not find anything.
    #
    # This does NOT necessarily mean the text is correct.
    # The AI acts as a fallback for mistakes the provider misses.
    print(
        f"{provider_name} found no corrections. "
        "Falling back to AI..."
    )

    return await ai_correct_text(
        text,
        native_language,
        target_language,
    )

