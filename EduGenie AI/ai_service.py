import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import settings


class TransientProviderError(ValueError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def _post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("error", {}).get("message", "Request rejected")
        except (json.JSONDecodeError, AttributeError):
            message = "Request rejected"
        if exc.code in {429, 500, 502, 503, 504}:
            retry_after = None
            try:
                retry_after = float(exc.headers.get("Retry-After"))
            except (AttributeError, TypeError, ValueError):
                pass
            raise TransientProviderError(
                f"AI provider is temporarily unavailable (HTTP {exc.code}): {message}",
                retry_after,
            ) from exc
        raise ValueError(f"AI provider returned HTTP {exc.code}: {message}") from exc
    except URLError as exc:
        raise ValueError("Could not connect to the AI provider. Check your network and try again.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("The AI provider returned an invalid response.") from exc


def _generate_gemini(
    prompt: str,
    response_mime_type: str | None,
    model: str | None = None,
) -> str:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured. Add it to the project's .env file.")

    payload = {
        "model": model or settings.gemini_model,
        "input": prompt,
        "store": False,
    }
    if response_mime_type:
        payload["response_format"] = {
            "type": "text",
            "mime_type": response_mime_type,
        }
    data = _post_json(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        payload,
        {"x-goog-api-key": settings.gemini_api_key},
    )

    texts = []
    for output in data.get("outputs", []):
        if isinstance(output, dict):
            if isinstance(output.get("text"), str):
                texts.append(output["text"])
            for content in output.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    texts.append(content["text"])
    if not texts:
        for step in data.get("steps", []):
            if isinstance(step, dict):
                for content in step.get("content", []):
                    if isinstance(content, dict) and isinstance(content.get("text"), str):
                        texts.append(content["text"])
    if texts:
        return "\n".join(texts).strip()
    raise ValueError("The AI provider returned no text. Try again with a shorter prompt.")


def _generate_local(prompt: str) -> str:
    if not settings.local_explanation_enabled:
        raise ValueError("GEMINI_API_KEY is not configured. Add it to the project's .env file.")
    data = _post_json(
        "http://127.0.0.1:11434/api/generate",
        {"model": settings.local_explanation_model, "prompt": prompt, "stream": False},
    )
    text = data.get("response", "").strip()
    if not text:
        raise ValueError("The local model returned no text.")
    return text


async def generate_text(
    prompt: str,
    *,
    response_mime_type: str | None = None,
    local: bool = False,
) -> str:
    if len(prompt) > settings.max_input_chars + 6000:
        raise ValueError(f"This request is too long. Keep it under {settings.max_input_chars} characters.")
    models = [None] if local else [settings.gemini_model]
    if (
        not local
        and settings.gemini_fallback_model
        and settings.gemini_fallback_model != settings.gemini_model
    ):
        models.append(settings.gemini_fallback_model)

    last_error = None
    for model in models:
        try:
            if local:
                return await asyncio.to_thread(_generate_local, prompt)
            return await asyncio.to_thread(
                _generate_gemini,
                prompt,
                response_mime_type,
                model,
            )
        except TransientProviderError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    raise ValueError("The AI provider could not complete this request.")