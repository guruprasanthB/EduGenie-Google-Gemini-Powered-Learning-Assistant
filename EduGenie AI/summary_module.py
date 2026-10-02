from ai_service import generate_text
from config import settings


async def summarize_text(text: str, style: str) -> str:
    if len(text) > settings.max_input_chars:
        raise ValueError(f"Keep text under {settings.max_input_chars} characters.")
    style_instructions = {
        "concise": "Write a concise summary in a few short paragraphs.",
        "detailed": "Write a detailed summary with the main argument, supporting points, and important terms.",
        "bullet_points": "Summarize as clear bullet points grouped by theme where useful.",
    }
    instruction = style_instructions.get(style, style_instructions["concise"])
    return await generate_text(
        "Summarize the source faithfully for a student. Do not add facts not present in it. "
        f"{instruction}\n\nSource text:\n{text}"
    )