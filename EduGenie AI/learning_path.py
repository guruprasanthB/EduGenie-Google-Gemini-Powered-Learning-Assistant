from ai_service import generate_text


async def get_learning_recommendations(topic: str, level: str, duration: int) -> str:
    prompt = (
        f"Create a practical {duration}-week learning path for a {level} learner studying {topic!r}. "
        "Use one clearly labeled section per week, ordered prerequisites, achievable weekly outcomes, a short "
        "practice activity, and a final review or project. Recommend resource types rather than inventing links. "
        "Keep the plan encouraging and realistic."
    )
    return await generate_text(prompt)