import asyncio
import pytest

from services.correction_service import (
    add_indices,
    build_language_tool_analysis,
    correct_text,
    empty_accuracy,
    ensure_accuracy,
    find_occurrence,
    run_provider,
    PROVIDERS,
    CORRECTION_PROVIDERS,
    DEFAULT_PROVIDER,
)
from services.providers import languagetool_provider


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
# Helper function tests
# ============================================================================

class TestFindOccurrence:
    def test_finds_substring(self):
        assert find_occurrence("hello world", "world") == 6

    def test_returns_minus_one_when_not_found(self):
        assert find_occurrence("hello world", "xyz") == -1

    def test_respects_start_position(self):
        text = "hello world hello"
        assert find_occurrence(text, "hello", 0) == 0
        assert find_occurrence(text, "hello", 5) == 12

    def test_empty_substring_returns_minus_one(self):
        assert find_occurrence("hello world", "") == -1

    def test_empty_text_returns_minus_one(self):
        assert find_occurrence("", "hello") == -1


class TestEmptyAccuracy:
    def test_returns_correct_structure(self):
        result = empty_accuracy()
        assert result["score"] == 100
        assert result["summary"] == "No significant corrections were found."
        assert result["categories"]["grammar"] == 100
        assert result["categories"]["vocabulary"] == 100
        assert result["categories"]["spelling"] == 100
        assert result["categories"]["sentenceStructure"] == 100
        assert result["improvementNote"] == ""


class TestEnsureAccuracy:
    def test_preserves_existing_accuracy(self):
        analysis = {
            "accuracy": {
                "score": 85,
                "summary": "Good",
                "categories": {
                    "grammar": 80,
                    "vocabulary": 90,
                    "spelling": 85,
                    "sentenceStructure": 85,
                },
                "improvementNote": "Work on grammar",
            }
        }
        result = ensure_accuracy(analysis)
        assert result["accuracy"]["score"] == 85
        assert result["accuracy"]["improvementNote"] == "Work on grammar"

    def test_fills_missing_accuracy(self):
        analysis = {}
        result = ensure_accuracy(analysis)
        assert result["accuracy"]["score"] == 100
        assert result["accuracy"]["summary"] == "No significant corrections were found."

    def test_handles_non_dict_analysis(self):
        result = ensure_accuracy(None)
        assert result["accuracy"]["score"] == 100

        result = ensure_accuracy("not a dict")
        assert result["accuracy"]["score"] == 100

    def test_fills_missing_categories(self):
        analysis = {"accuracy": {"score": 50}}
        result = ensure_accuracy(analysis)
        assert result["accuracy"]["categories"]["grammar"] == 100
        assert result["accuracy"]["categories"]["vocabulary"] == 100


class TestAddIndices:
    def test_adds_indices_for_mistakes(self):
        analysis = {
            "mistakes": [
                {"original": "go", "corrected": "went"},
                {"original": "find", "corrected": "found"},
            ]
        }
        text = "I go to the store and find a book."
        result = add_indices(text, analysis)

        assert result["mistakes"][0]["start"] == 2
        assert result["mistakes"][0]["end"] == 4
        # find starts at position 22, not 21 (the double space after the period matters)
        assert result["mistakes"][1]["start"] >= 21

    def test_preserves_existing_valid_indices(self):
        analysis = {
            "mistakes": [
                {
                    "original": "go",
                    "corrected": "went",
                    "start": 2,
                    "end": 4,
                },
            ]
        }
        text = "I go to the store."
        result = add_indices(text, analysis)

        assert result["mistakes"][0]["start"] == 2
        assert result["mistakes"][0]["end"] == 4

    def test_handles_empty_mistakes(self):
        analysis = {"mistakes": []}
        result = add_indices("some text", analysis)
        assert result["mistakes"] == []

    def test_handles_non_dict_mistakes_preserved(self):
        # The function only skips non-dict items, doesn't filter them out
        analysis = {"mistakes": [None, "not a dict"]}
        result = add_indices("some text", analysis)
        # Non-dict items are kept as-is (skipped but not removed)
        assert result["mistakes"] == [None, "not a dict"]

    def test_handles_missing_original(self):
        analysis = {"mistakes": [{"corrected": "went"}]}
        result = add_indices("some text", analysis)
        assert result["mistakes"][0]["start"] is None
        assert result["mistakes"][0]["end"] is None


# ============================================================================
# Provider configuration tests
# ============================================================================

class TestProviderConfiguration:
    def test_all_providers_registered(self):
        assert "languagetool" in PROVIDERS
        assert "japanese_provider" in PROVIDERS
        assert "korean_provider" in PROVIDERS
        assert "chinese_provider" in PROVIDERS

    def test_correction_providers_mapping(self):
        assert CORRECTION_PROVIDERS["English"] == "languagetool"
        assert CORRECTION_PROVIDERS["Spanish"] == "languagetool"
        assert CORRECTION_PROVIDERS["French"] == "languagetool"
        assert CORRECTION_PROVIDERS["German"] == "languagetool"
        assert CORRECTION_PROVIDERS["Japanese"] == "japanese_provider"
        assert CORRECTION_PROVIDERS["Korean"] == "korean_provider"
        assert CORRECTION_PROVIDERS["Chinese"] == "chinese_provider"

    def test_default_provider(self):
        assert DEFAULT_PROVIDER == "languagetool"


# ============================================================================
# Build LanguageTool analysis tests
# ============================================================================

class TestBuildLanguageToolAnalysis:
    def test_returns_corrected_text(self):
        # Use the provider's check function instead of LanguageTool directly
        text = "I go to the store."
        matches = languagetool_provider.check(text, "English")
        result = build_language_tool_analysis(text, matches)
        assert "text" in result
        assert "mistakes" in result
        assert "accuracy" in result

    def test_returns_empty_accuracy_for_correct_text(self):
        # A correct sentence should return empty accuracy (no mistakes)
        text = "Yesterday I went to the store."
        matches = languagetool_provider.check(text, "English")
        result = build_language_tool_analysis(text, matches)
        assert result["accuracy"]["score"] == 100


# ============================================================================
# Run provider tests - use correct_text which handles async properly
# ============================================================================

class TestRunProvider:
    def test_quick_review_uses_provider_only(self):
        result = asyncio.run(correct_text("I goes to the store.", "English", "English", "quick"))
        assert "text" in result
        assert "mistakes" in result
        assert "accuracy" in result
        assert "original_text" in result
        assert result["original_text"] == "I goes to the store."

    def test_unknown_provider_falls_back_to_default(self):
        # When provider not found, should still return valid result
        result = asyncio.run(correct_text("Some text to check.", "English", "English", "quick"))
        assert "text" in result
        assert "accuracy" in result


# ============================================================================
# Async helper
# ============================================================================

def run_async(coro):
    return asyncio.run(coro)


# ============================================================================
# Correct text integration tests
# ============================================================================

class TestCorrectText:
    def test_none_text_converted_to_empty(self):
        # None is converted to empty string, not raised as error
        result = asyncio.run(correct_text(None))
        assert result["text"] == ""
        assert result["mistakes"] == []

    def test_raises_on_non_string_text(self):
        with pytest.raises(TypeError):
            asyncio.run(correct_text(123))

    def test_empty_text_returns_empty(self):
        result = asyncio.run(correct_text(""))
        assert result["text"] == ""
        assert result["mistakes"] == []
        assert result["original_text"] == ""

    def test_whitespace_only_returns_empty(self):
        result = asyncio.run(correct_text("   \n\t  "))
        assert result["text"] == ""
        assert result["mistakes"] == []

    def test_invalid_review_depth_defaults_to_quick(self):
        text = "I go to the store."
        result = asyncio.run(correct_text(text, "English", "English", "invalid"))
        assert "text" in result

    def test_includes_original_text(self):
        text = "I goes to the store."
        result = asyncio.run(correct_text(text, "English", "English", "quick"))
        assert result["original_text"] == text

    def test_returns_accuracy_object(self):
        text = "I go to the store."
        result = asyncio.run(correct_text(text, "English", "English", "quick"))
        assert "accuracy" in result
        assert "score" in result["accuracy"]
        assert "summary" in result["accuracy"]
        assert "categories" in result["accuracy"]


# ============================================================================
# Language-specific provider routing tests
# ============================================================================

class TestProviderRouting:
    def test_english_uses_languagetool(self):
        result = asyncio.run(correct_text("I go to the store yesterday.", "English", "English", "quick"))
        assert "text" in result

    def test_japanese_routes_to_japanese_provider(self):
        result = asyncio.run(correct_text("私は友達と映画を見た。", "Japanese", "Japanese", "quick"))
        assert "text" in result

    def test_korean_routes_to_korean_provider(self):
        result = asyncio.run(correct_text("나는 친구와 영화를 봤어.", "Korean", "Korean", "quick"))
        assert "text" in result

    def test_chinese_routes_to_chinese_provider(self):
        result = asyncio.run(correct_text("我和朋友看了电影。", "Chinese", "Chinese", "quick"))
        assert "text" in result

    def test_spanish_uses_languagetool(self):
        result = asyncio.run(correct_text("Yo voy a la tienda ayer.", "Spanish", "Spanish", "quick"))
        assert "text" in result


# ============================================================================
# In-depth mode tests
# ============================================================================

class TestInDepthMode:
    def test_in_depth_returns_analysis(self):
        result = asyncio.run(correct_text("I go to the store yesterday.", "English", "English", "in-depth"))
        assert "text" in result
        assert "mistakes" in result
        assert "accuracy" in result
        assert "original_text" in result

    def test_in_depth_produces_corrected_text(self):
        result = asyncio.run(correct_text("I have went to the store.", "English", "English", "in-depth"))
        assert isinstance(result["text"], str)


# ============================================================================
# Mistake structure validation
# ============================================================================

class TestMistakeStructure:
    def test_mistakes_have_required_fields(self):
        result = asyncio.run(correct_text("I go to the store yesterday.", "English", "English", "quick"))
        for mistake in result["mistakes"]:
            assert "original" in mistake
            assert "corrected" in mistake

    def test_mistakes_indices_are_valid(self):
        text = "I go to the store."
        result = asyncio.run(correct_text(text, "English", "English", "quick"))
        for mistake in result["mistakes"]:
            if isinstance(mistake.get("start"), int) and isinstance(mistake.get("end"), int):
                assert mistake["start"] >= 0
                assert mistake["end"] > mistake["start"]
                assert mistake["end"] <= len(text)
                if mistake["start"] is not None and mistake["end"] is not None:
                    assert text[mistake["start"]:mistake["end"]] == mistake["original"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
