import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()


client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)


async def correct_text(text, native_language='english', target_language='english'):

    print("Calling AI model...")

    print("Text received:", repr(text))
    print(f"Native language set to: {native_language}\nTarget language set to: {target_language}")

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""
You are a multilingual language tutor working with {target_language}.

Correct the grammar of the user's text while preserving the original meaning and tone.

Return ONLY valid JSON.

The JSON must use exactly this structure:

{{
    "text": "The complete corrected version of the user's text in {target_language}.",
    "mistakes": [
        {{
            "original": "The exact incorrect text from the user's input in {target_language}.",
            "corrected": "The corrected version of that text in {target_language}.",
            "explanation": "Explain in one or two concise sentences suitable for a language learner why the original was incorrect in {native_language}.",
            "category": "verb_conjugation (written in {native_language})"
        }}
    ]
}}

Rules:
- "text" must contain the complete corrected text in {target_language}.
- Each grammar mistake must be a separate object in the "mistakes" array.
- "original" must exactly match the incorrect text in the user's input in {target_language}.
- "corrected" must contain the replacement text in {target_language}.
- "explanation" must clearly explain the grammar rule or reason for the correction and must be written in {native_language}
- "category" must be written in {native_language}
- Preserve the language of the user's original text.
- Do not translate the text.
- Do not change correct text unnecessarily.
- If there are no mistakes, return an empty "mistakes" array.
- Do not include markdown.
- Do not include code fences.
- Do not include any text before or after the JSON object.
"""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        extra_body={
            "reasoning_split": True
        }
    )

    print("AI model finished")

    res = response.choices[0].message.content


# Handle cases where the AI returns invalid JSON by raising a ValueError with a descriptive message.
    try:
        data = json.loads(res)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")

    data['original_text'] = text

    return data


async def translate_word(
    text,
    source_language="english",
    target_language="english",
):
    response = client.chat.completions.create(
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

Rules:
- Translate only.
- Do not explain.
- Do not include markdown.
- Return only JSON.
- "part_of_speech" should be one of:
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
"""
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

    res = response.choices[0].message.content

    try:
        return json.loads(res)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")