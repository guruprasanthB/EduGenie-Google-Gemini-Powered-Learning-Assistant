from ai_service import generate_text
from config import settings


async def explain_concept(topic: str, level: str) -> str:
    prompt = (
        f"Explain {topic!r} to a {level} learner. Start with a plain-language definition, then build the idea "
        "step by step. Include one concrete example, explain why the concept matters, and finish with one short "
        "check-your-understanding question. Be accurate and avoid assuming knowledge beyond the stated level."
    )
    return await generate_text(
        prompt,
        local=not settings.gemini_api_key and settings.local_explanation_enabled,
    )