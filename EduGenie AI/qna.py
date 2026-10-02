from ai_service import generate_text
from config import settings


async def answer_question(question: str) -> str:
    if len(question) > settings.max_input_chars:
        raise ValueError(f"Keep your question under {settings.max_input_chars} characters.")
    prompt = (
        "You are EduGenie, a careful and encouraging study assistant. Answer the student's question directly, "
        "explain unfamiliar terms, use a short example when it helps, and distinguish uncertainty from fact. "
        "Keep the response easy to scan.\n\nStudent question:\n" + question
    )
    return await generate_text(prompt)