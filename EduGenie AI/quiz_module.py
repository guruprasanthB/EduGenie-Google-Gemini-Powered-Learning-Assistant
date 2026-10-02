import json
import re

from ai_service import generate_text
from config import settings


def _parse_quiz(text: str) -> list[dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("The AI returned an unreadable quiz. Please try again.")
        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("The AI returned an unreadable quiz. Please try again.") from exc

    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list):
        raise ValueError("The AI returned an invalid quiz. Please try again.")

    normalized = []
    for item in questions:
        if not isinstance(item, dict) or not isinstance(item.get("question"), str):
            continue
        options = item.get("options", [])
        if not isinstance(options, list):
            continue
        normalized.append({
            "question": item["question"],
            "options": [str(option) for option in options],
            "answer": str(item.get("answer", "Not provided")),
            "explanation": str(item.get("explanation", "")),
        })
    if not normalized:
        raise ValueError("The AI returned an empty quiz. Please try again.")
    return normalized


async def generate_quiz(text: str, question_count: int) -> dict:
    if len(text) > settings.max_input_chars:
        raise ValueError(f"Keep study material under {settings.max_input_chars} characters.")
    prompt = (
        f"Create exactly {question_count} useful multiple-choice questions based only on the study material below. "
        "Return valid JSON with this shape: {\"questions\":[{\"question\":\"...\",\"options\":[\"...\",\"...\",\"...\",\"...\"],\"answer\":\"the full correct option text\",\"explanation\":\"...\"}]}. "
        "Make distractors plausible and do not include information absent from the material.\n\nStudy material:\n" + text
    )
    response = await generate_text(prompt, response_mime_type="application/json")
    return {"questions": _parse_quiz(response)[:question_count]}