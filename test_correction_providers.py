import asyncio

from services.correction_service import (
    build_language_tool_analysis,
    merge_corrections,
)
from services.providers import languagetool_provider
from services.ai_service import ai_correct_text


TEST_TEXT = """Yesterday I go to the library because I need to studied for my exam.

When I arrived, there was many students sitting at the tables.

I find a quiet place near the window and start reading my textbook.

After about an hour, I realize that I don't understood some of the topics very well,

so I decided to ask my friend for help.

She have studied this subject before and she explain everything very clearly.

We spent almost two hours reviewing the material, and she give me some useful advice

about how I can improve my studying habits.

Before we leave, she told me that I should practices the difficult problems more often.

I was very tired when I finally went home, but I knows that I need to study more

if I want to do well on the exam.
"""


# ============================================================================
# HELPERS
# ============================================================================

def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_mistakes(mistakes):
    for mistake in mistakes:
        print(
            f"ORIGINAL:      {mistake.get('original')}\n"
            f"CORRECTED:     {mistake.get('corrected')}\n"
            f"ORIGINAL FULL: {mistake.get('original_full')}\n"
            f"CORRECTED FULL:{mistake.get('corrected_full')}\n"
            f"PROVIDER:      {mistake.get('provider')}\n"
            f"START:         {mistake.get('start')}\n"
            f"END:           {mistake.get('end')}\n"
            + "-" * 80
        )


def print_short_mistakes(mistakes):
    for mistake in mistakes:
        print(
            f"[{mistake.get('provider', 'unknown')}] "
            f"{mistake.get('original')!r} "
            f"-> "
            f"{mistake.get('corrected')!r}"
        )


def apply_corrections(text, corrections):
    """
    Apply corrections from right to left so that changing one span
    does not invalidate the indices of corrections earlier in the text.
    """

    sorted_corrections = sorted(
        corrections,
        key=lambda correction: correction["start"],
        reverse=True,
    )

    corrected_text = text

    for correction in sorted_corrections:
        start = correction["start"]
        end = correction["end"]
        replacement = correction["corrected"]

        corrected_text = (
            corrected_text[:start]
            + replacement
            + corrected_text[end:]
        )

    return corrected_text


# ============================================================================
# LANGUAGETOOL
# ============================================================================

def test_language_tool():
    print_header("LANGUAGETOOL")

    print("Starting LanguageTool for en-US...")

    matches = languagetool_provider.check(
        TEST_TEXT,
        "English",
    )

    print(f"Found {len(matches)} corrections\n")

    for match in matches:
        if not match.replacements:
            continue

        original = TEST_TEXT[
            match.offset:
            match.offset + match.error_length
        ]

        corrected = match.replacements[0]

        print(f"ORIGINAL:      {original}")
        print(f"CORRECTED:     {corrected}")
        print(f"RULE:          {match.rule_id}")
        print(f"MESSAGE:       {match.message}")
        print("-" * 80)

    return matches


# ============================================================================
# MINIMAX
# ============================================================================

async def test_minimax(review_mode):
    title = review_mode.upper()

    print_header(f"MINIMAX — {title} REVIEW")

    result = await ai_correct_text(
        TEST_TEXT,
        "English",
        "English",
        review_mode,
    )

    print_header(f"{title} REVIEW — CORRECTED TEXT")
    print(result["text"])

    print_header(f"{title} REVIEW — MISTAKES")

    print(
        f"Found {len(result['mistakes'])} corrections\n"
    )

    print_mistakes(result["mistakes"])

    print_header(f"{title} REVIEW — ACCURACY")

    accuracy = result["accuracy"]

    print(f"Score: {accuracy['score']}")
    print(f"Summary: {accuracy['summary']}")
    print(f"Categories: {accuracy['categories']}")
    print(f"Improvement: {accuracy['improvementNote']}")

    return result


# ============================================================================
# MERGE TEST
# ============================================================================

def test_merge(language_tool_analysis, minimax_result, review_mode):
    print_header(
        f"LANGUAGETOOL + MINIMAX {review_mode.upper()} — MERGING"
    )

    merged = merge_corrections(
        language_tool_analysis["mistakes"],
        minimax_result["mistakes"],
        TEST_TEXT,
    )

    print(
        f"LanguageTool corrections: "
        f"{len(language_tool_analysis['mistakes'])}"
    )

    print(
        f"MiniMax corrections: "
        f"{len(minimax_result['mistakes'])}"
    )

    print(
        f"Merged corrections: "
        f"{len(merged)}"
    )

    print_header(
        f"LANGUAGETOOL + MINIMAX {review_mode.upper()} — MERGED"
    )

    print_mistakes(merged)

    return merged


# ============================================================================
# APPLY MERGED CORRECTIONS
# ============================================================================

def test_apply_corrections(merged, review_mode):
    print_header(
        f"{review_mode.upper()} — APPLYING MERGED CORRECTIONS"
    )

    corrected_text = apply_corrections(
        TEST_TEXT,
        merged,
    )

    print(corrected_text)

    return corrected_text


# ============================================================================
# VALIDATION
# ============================================================================

def validate_merged_corrections(
    original_text,
    merged,
    corrected_text,
    review_mode,
):
    print_header(
        f"{review_mode.upper()} — MERGE VALIDATION"
    )

    print(
        f"Original length:  {len(original_text)}"
    )

    print(
        f"Corrected length: {len(corrected_text)}"
    )

    print(
        f"Merged corrections: {len(merged)}"
    )

    # Check that every correction has the expected fields.
    required_fields = [
        "original",
        "corrected",
        "start",
        "end",
        "provider",
    ]

    missing_fields = []

    for index, correction in enumerate(merged):
        for field in required_fields:
            if field not in correction:
                missing_fields.append(
                    f"Correction {index}: missing '{field}'"
                )

    if missing_fields:
        print("\n❌ MISSING FIELDS")

        for error in missing_fields:
            print(error)
    else:
        print("\n✅ All merged corrections contain required fields.")

    # Check that the spans match the original text.
    invalid_spans = []

    for index, correction in enumerate(merged):
        start = correction["start"]
        end = correction["end"]
        expected_original = correction["original"]

        actual_original = original_text[start:end]

        if actual_original != expected_original:
            invalid_spans.append(
                {
                    "index": index,
                    "expected": expected_original,
                    "actual": actual_original,
                    "start": start,
                    "end": end,
                }
            )

    if invalid_spans:
        print("\n❌ INVALID INDICES")

        for error in invalid_spans:
            print(
                f"Correction {error['index']}: "
                f"expected {error['expected']!r}, "
                f"but original text contains {error['actual']!r} "
                f"at {error['start']}:{error['end']}"
            )
    else:
        print(
            "✅ All correction indices point to the expected "
            "text in the original."
        )

    # Check for overlapping merged corrections.
    sorted_corrections = sorted(
        merged,
        key=lambda correction: correction["start"],
    )

    overlaps = []

    for current, next_correction in zip(
        sorted_corrections,
        sorted_corrections[1:],
    ):
        if current["end"] > next_correction["start"]:
            overlaps.append(
                (
                    current,
                    next_correction,
                )
            )

    if overlaps:
        print("\n⚠️ OVERLAPPING MERGED CORRECTIONS")

        for first, second in overlaps:
            print(
                f"'{first['original']}' "
                f"({first['start']}:{first['end']})"
            )

            print(
                f"'{second['original']}' "
                f"({second['start']}:{second['end']})"
            )

            print("-" * 80)
    else:
        print(
            "✅ No overlapping corrections remain "
            "in the merged result."
        )

    print("\n" + "-" * 80)
    print("FINAL VALIDATION RESULT")
    print("-" * 80)

    if (
        not missing_fields
        and not invalid_spans
        and not overlaps
    ):
        print("✅ MERGE PASSED VALIDATION")
    else:
        print("⚠️ MERGE NEEDS ATTENTION")


# ============================================================================
# COMPARISON
# ============================================================================

def compare_results(
    language_tool_analysis,
    quick_result,
    indepth_result,
    quick_merged,
    indepth_merged,
):
    print_header("FINAL COMPARISON")

    print(
        f"LanguageTool corrections:       "
        f"{len(language_tool_analysis['mistakes'])}"
    )

    print(
        f"MiniMax Quick corrections:      "
        f"{len(quick_result['mistakes'])}"
    )

    print(
        f"MiniMax In-Depth corrections:   "
        f"{len(indepth_result['mistakes'])}"
    )

    print()

    print(
        f"LT + Quick merged corrections:  "
        f"{len(quick_merged)}"
    )

    print(
        f"LT + In-Depth merged corrections:"
        f" {len(indepth_merged)}"
    )

    print()

    print(
        f"Quick score:                     "
        f"{quick_result['accuracy']['score']}"
    )

    print(
        f"In-Depth score:                  "
        f"{indepth_result['accuracy']['score']}"
    )

    print_header("QUICK MERGED CORRECTIONS")

    print_short_mistakes(quick_merged)

    print_header("IN-DEPTH MERGED CORRECTIONS")

    print_short_mistakes(indepth_merged)


# ============================================================================
# MAIN
# ============================================================================

async def main():

    # ------------------------------------------------------------------------
    # 1. LanguageTool
    # ------------------------------------------------------------------------

    language_tool_matches = test_language_tool()

    language_tool_analysis = build_language_tool_analysis(
        TEST_TEXT,
        language_tool_matches,
    )

    print_header("LANGUAGETOOL WRITE RIGHT ANALYSIS")

    print(
        f"Corrections in WriteRight format: "
        f"{len(language_tool_analysis['mistakes'])}"
    )

    # ------------------------------------------------------------------------
    # 2. MiniMax Quick
    # ------------------------------------------------------------------------

    quick_result = await test_minimax("quick")

    # ------------------------------------------------------------------------
    # 3. MiniMax In-Depth
    # ------------------------------------------------------------------------

    indepth_result = await test_minimax("in-depth")

    # ------------------------------------------------------------------------
    # 4. Merge Quick
    # ------------------------------------------------------------------------

    quick_merged = test_merge(
        language_tool_analysis,
        quick_result,
        "quick",
    )

    # ------------------------------------------------------------------------
    # 5. Merge In-Depth
    # ------------------------------------------------------------------------

    indepth_merged = test_merge(
        language_tool_analysis,
        indepth_result,
        "in-depth",
    )

    # ------------------------------------------------------------------------
    # 6. Apply Quick merged corrections
    # ------------------------------------------------------------------------

    quick_corrected_text = test_apply_corrections(
        quick_merged,
        "quick",
    )

    # ------------------------------------------------------------------------
    # 7. Apply In-Depth merged corrections
    # ------------------------------------------------------------------------

    indepth_corrected_text = test_apply_corrections(
        indepth_merged,
        "in-depth",
    )

    # ------------------------------------------------------------------------
    # 8. Validate Quick
    # ------------------------------------------------------------------------

    validate_merged_corrections(
        TEST_TEXT,
        quick_merged,
        quick_corrected_text,
        "quick",
    )

    # ------------------------------------------------------------------------
    # 9. Validate In-Depth
    # ------------------------------------------------------------------------

    validate_merged_corrections(
        TEST_TEXT,
        indepth_merged,
        indepth_corrected_text,
        "in-depth",
    )

    # ------------------------------------------------------------------------
    # 10. Final comparison
    # ------------------------------------------------------------------------

    compare_results(
        language_tool_analysis,
        quick_result,
        indepth_result,
        quick_merged,
        indepth_merged,
    )

    # ------------------------------------------------------------------------
    # 11. Final summary
    # ------------------------------------------------------------------------

    print_header("NEXT STEP")

    print(
        "Review the merged output above."
    )

    print(
        "The important things to verify are:"
    )

    print(
        "1. Duplicate corrections are removed."
    )

    print(
        "2. Contextual MiniMax corrections replace weaker "
        "LanguageTool corrections when appropriate."
    )

    print(
        "3. Independent LanguageTool corrections are preserved."
    )

    print(
        "4. Merged correction indices point to the correct "
        "locations in the original text."
    )

    print(
        "5. Applying the merged corrections produces valid "
        "corrected text without spacing or text corruption."
    )


if __name__ == "__main__":
    asyncio.run(main())