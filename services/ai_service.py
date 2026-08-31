import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()


client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


def _parse_json_response(response):
    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI returned an empty response")

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("AI returned invalid JSON") from error


def _add_mistake_defaults(data, original_text):
    if not isinstance(data, dict):
        raise ValueError("AI returned an invalid response")

    data["original_text"] = original_text

    if not isinstance(data.get("mistakes"), list):
        data["mistakes"] = []

    for mistake in data["mistakes"]:
        if not isinstance(mistake, dict):
            continue

        mistake["explanation"] = mistake.get("explanation")
        mistake["category"] = mistake.get("category")
        mistake["loading"] = False
        mistake.setdefault("start", None)
        mistake.setdefault("end", None)

    if not data.get("accuracy"):
        data["accuracy"] = {
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

    return data


async def ai_correct_text(
    text,
    native_language="English",
    target_language="English",
):
    print("Calling AI model...")

    if not target_language:
        target_language = "English"

    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""
You are a multilingual language tutor.

The student speaks {native_language} and is learning {target_language}.

Correct the student's writing while preserving its meaning, tone,
and original language.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "text": "complete corrected text",
    "mistakes": [
        {{
            "original": "smallest incorrect word or phrase",
            "corrected": "replacement for that word or phrase",
            "original_full": "full original context with the incorrect text surrounded by **",
            "corrected_full": "full corrected context with the corrected text surrounded by **"
        }}
    ],
    "accuracy": {{
        "score": 0,
        "summary": "",
        "categories": {{
            "grammar": 0,
            "vocabulary": 0,
            "spelling": 0,
            "sentenceStructure": 0
        }},
        "improvementNote": ""
    }}
}}

Rules:

- Return only JSON.
- Do not translate the text.
- Preserve the language of the user's original text.
- Do not unnecessarily change correct text.
- "text" must contain the complete corrected text.
- "original" must contain only the smallest incorrect word or phrase.
- "corrected" must contain only its replacement.
- Do not put ** inside "original" or "corrected".
- "original_full" must contain the original text with the incorrect
  word or phrase surrounded by **.
- "corrected_full" must contain the corrected text with the correction
  surrounded by **.
- Each mistake must be a separate object.
- If there are no mistakes, return an empty mistakes array.
- accuracy is always required.
- accuracy.score must be an integer from 0 to 100.
- accuracy.categories must contain grammar, vocabulary, spelling,
  and sentenceStructure as integers from 0 to 100.
- summary and improvementNote must be written in {native_language}.
- Do not include markdown or code fences.
""",
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        extra_body={
            "reasoning_split": True,
        },
    )

    print("AI model finished")

    data = _parse_json_response(response)

    return _add_mistake_defaults(data, text)


async def translate_word(
    text,
    source_language="English",
    target_language="English",
):
    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""
You are an expert multilingual dictionary.

Translate the user's word or short phrase from
{source_language} to {target_language}.

Return ONLY valid JSON.

The JSON must exactly match:

{{
    "original_text": "The exact text entered by the user.",
    "interpreted_text": "The correctly spelled source-language word or phrase.",
    "translation": "The translated word.",
    "part_of_speech": "noun",
    "source_language": "english",
    "target_language": "german"
}}

Translate only.
Do not explain.
Do not include markdown.
Do not include code fences.

"part_of_speech" must be one of:

noun
verb
adjective
adverb
pronoun
preposition
conjunction
interjection
article
phrase
""",
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        extra_body={
            "reasoning_split": True,
        },
    )

    return _parse_json_response(response)


async def generate_explanation(
    original,
    corrected,
    native_language="English",
    target_language="English",
):
    print("Calling AI explanation model...")

    response = await client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""
You are a multilingual language tutor.

The student speaks {native_language} and is learning {target_language}.

Explain the correction concisely in {native_language}.

Return ONLY valid JSON:

{{
    "explanation": "one or two concise sentences",
    "category": "category of mistake"
}}

The explanation must clearly explain why the original was incorrect.

The category must be written in {native_language}.

Do not include markdown.
Do not include code fences.
Do not include any text outside the JSON object.
""",
            },
            {
                "role": "user",
                "content": f"""
Original:

{original}

Corrected:

{corrected}
""",
            },
        ],
        extra_body={
            "reasoning_split": True,
        },
    )

    return _parse_json_response(response)
