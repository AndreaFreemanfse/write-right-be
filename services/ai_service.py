import json
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastapi import HTTPException

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
- Each grammar mistake must be a separate object in the "mistakes" array.
- "accuracy" must always be included.
- "score" must be an integer from 0 to 100 representing the learner's overall writing proficiency and ability to communicate effectively.
- Use this scoring guide:
  - 90-100: Nearly error-free, clear, and natural.
  - 80-89: Clear and effective with only minor mistakes.
  - 70-79: Several noticeable mistakes, but the meaning remains clear.
  - 60-69: Frequent mistakes, but most of the text is still understandable.
  - 50-59: Many significant mistakes that sometimes interfere with understanding.
  - Below 50: The text is consistently difficult to understand.
- A few grammar mistakes should not dramatically reduce the score if the meaning remains clear.
- Consider overall communication, clarity, vocabulary, grammar, and fluency together rather than simply counting mistakes.
- Reserve scores below 50 for writing that is genuinely difficult to understand because of frequent or severe errors.
- Category scores should reflect the learner's overall proficiency in that area rather than the percentage of words that were incorrect.
- "categories" must include integer scores from 0 to 100 for grammar, vocabulary, spelling, and sentenceStructure.
- "improvementNote" must be one concise sentence in {native_language} describing the single most important area for improvement.
- "original" must contain ONLY the smallest incorrect word or phrase that requires correction in the {target_language}. Never return an entire sentence unless the entire sentence itself is the mistake. It must never contain '**' marks.
- "corrected" must contain ONLY the replacement for the incorrect word or phrase in {target_language}. It must correspond exactly to "original" and never contain surrounding words that were already correct. It must never contain '**' marks.
- "corrected_full" must only contain words from the corrected version of the text. The corrected word from the 'corrected' field must have '**' directly on both sides of the word.
- "original_full" must exactly match 'corrected_full' except for the word inside the '**' marks.
- Preserve the language of the user's original text.
- Keep both "original" and "corrected" as short as possible while preserving the grammatical correction.
- If the input text is completely written in a language other than the target language, ignore all other input and return '{{ "error": "MISMATCH"}}'.
- "text" must contain the complete corrected text in {target_language}.
- "summary" must be one concise sentence written in {native_language}.
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

# Handle cases where the AI returns invalid JSON by raising a ValueError with a descriptive message.
    try:
        data = json.loads(res)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")

    if 'error' in data:
        if data['error'] == 'MISMATCH':
            raise HTTPException( status_code=400, detail=f"Written language does not match target language." )
            
    data['original_text'] = text

    for m in data['mistakes']:
        m['explanation'] = None
        m['category'] = None
        m['loading'] = False

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
