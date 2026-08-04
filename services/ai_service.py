import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()


client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)


async def correct_text(text, native_language='English', target_language='English'):

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
            "corrected": "The corrected version of that text in {target_language}."
            "corrected_full": "The corrected version of the text in {target_language} with '**' direcly on both sides of the word from the 'corrected' field, also containing the full context from the corrected text in the 'text' field."
            "original_full": "An exact copy of the 'corrected_full' field, but with the word from the 'original' field inside of the '**' marks."
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

Example:

User input:
Ich gehen nach Hause.

Correct response for the mistake field:

"original": "gehen"
"corrected": "gehe"
"original_full": "Ich **gehen** nach Hause."
"corrected_full": "Ich **gehe** nach Hause."

NOT

"original": "Ich **gehen** nach Hause."
"corrected": "Ich **gehe** nach Hause."
"original_full": "Ich gehen nach Hause."
"corrected_full": "Ich gehe nach Hause."


Example:

User input:
I no speak English good.

Correct response:

"text": "I don't speak English well."

"mistakes": [
    "original": "no"
    "corrected": "don't"
    "original_full": "I **no** speak English well."
    "corrected_full": "I **don't** speak English well."

    "original": "good"
    "corrected": "well"
    "original_full": "I don't speak English **good**."
    "corrected_full": "I don't speak English **well**."
]

NOT

"text": "I don't speak English well."

"mistakes": [
    "original": "no"
    "corrected": "don't"
    "original_full": "I **no** speak English good."
    "corrected_full": "I **don't** speak English good."

    "original": "good"
    "corrected": "well"
    "original_full": "I no speak English **good**."
    "corrected_full": "I no speak English **well**."
]


Rules:
- "text" must contain the complete corrected text in {target_language}.
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
- "summary" must be one concise sentence written in {native_language}.
- "categories" must include integer scores from 0 to 100 for grammar, vocabulary, spelling, and sentenceStructure.
- "improvementNote" must be one concise sentence in {native_language} describing the single most important area for improvement.
- "original" must contain ONLY the smallest incorrect word or phrase that requires correction in the {target_language}. Never return an entire sentence unless the entire sentence itself is the mistake. It must never contain '**' marks.
- "corrected" must contain ONLY the replacement for the incorrect word or phrase in {target_language}. It must correspond exactly to "original" and never contain surrounding words that were already correct. It must never contain '**' marks.
- "corrected_full" must only contain words from the corrected version of the text. The corrected word from the 'corrected' field must have '**' directly on both sides of the word.
- "original_full" must exactly match 'corrected_full' except for the word inside the '**' marks.
- Preserve the language of the user's original text.
- Keep both "original" and "corrected" as short as possible while preserving the grammatical correction.
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

    for m in data['mistakes']:
        m['explanation'] = None
        m['category'] = None
        m['loading'] = False

    return data


async def translate_word(
    text,
    source_language="English",
    target_language="English",
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


async def generate_explanation(original, corrected, native_language='English', target_language='English'):

    print("Calling AI model...")

    print("Original text received:", repr(original))
    print("Corrected text received:", repr(corrected))
    print(f"Native language set to: {native_language}\nTarget language set to: {target_language}")

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""
You are a multilingual language tutor working with a student who speaks {native_language} and is learning {target_language}.

You will recieve an original version of a text and a corrected version of the same text.
The word that has been corrected will have '**' direcly on either side of the word in both versions of the text.

Please provide a concise explanation of the correction in {native_language}.

Please provide a category for the type of mistake made in {native_language}.

Return ONLY valid JSON.

The JSON must use exactly this structure:

{{
    "explanation": "Explain in one or two concise sentences suitable for a language learner why the original was incorrect in {native_language}.",
    "category": "category of mistake written in {native_language}."
}}


Rules:
- "explanation" must clearly explain the grammar rule or reason for the correction and must be written in {native_language}.
- "category" must be written in {native_language}. Examples of English categories include irregular verb, capitilization, spelling, verb agreement, etc.
- Do not translate the text.
- Do not include markdown.
- Do not include code fences.
- Do not include any text before or after the JSON object.
"""
            },
            {
                "role": "user",
                "content": f"""
Original:
{original}

Corrected:
{corrected}
"""
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

    return data