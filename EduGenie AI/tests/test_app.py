import unittest
from dataclasses import replace
import json
from unittest.mock import AsyncMock, patch

import ai_service
import main
from quiz_module import generate_quiz
from schemas import (
    ExplainRequest,
    LearningPathRequest,
    QARequest,
    QuizRequest,
    SummaryRequest,
)


class AppRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_reports_configured_model(self):
        response = await main.health()

        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["model"], "gemini-3.5-flash-lite")

    async def test_question_answering_route(self):
        with patch("main.answer_question", new=AsyncMock(return_value="Answer")):
            response = await main.qa(QARequest(question="Why is the sky blue?"))

        self.assertEqual(response, {"success": True, "result": "Answer"})

    async def test_explanation_route(self):
        with patch("main.explain_concept", new=AsyncMock(return_value="Explanation")):
            response = await main.explain(ExplainRequest(topic="gravity", level="beginner"))

        self.assertEqual(response, {"success": True, "result": "Explanation"})

    async def test_quiz_route(self):
        text = "A sufficiently long block of study material for quiz generation."
        quiz_result = {"questions": [{"question": "Q", "options": [], "answer": "A"}]}
        with patch("main.generate_quiz", new=AsyncMock(return_value=quiz_result)):
            response = await main.quiz(QuizRequest(text=text, question_count=3))

        self.assertEqual(response, {"success": True, "quiz": quiz_result})

    async def test_summary_route(self):
        text = "A sufficiently long block of study material for summarization."
        with patch("main.summarize_text", new=AsyncMock(return_value="Summary")):
            response = await main.summarize(SummaryRequest(text=text, style="concise"))

        self.assertEqual(response, {"success": True, "result": "Summary"})

    async def test_learning_path_route(self):
        with patch("main.get_learning_recommendations", new=AsyncMock(return_value="Plan")):
            response = await main.learning_recommendations(
                LearningPathRequest(topic="algebra", level="beginner", duration=4)
            )

        self.assertEqual(response, {"success": True, "result": "Plan"})

    async def test_transient_provider_response_preserves_quota_and_retry_hint(self):
        message = "HTTP 429: free-tier daily quota exceeded"
        response = await main.transient_provider_error_handler(
            None,
            ai_service.TransientProviderError(message, retry_after=59),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["retry-after"], "59")
        self.assertEqual(response.body, b'{"error":"HTTP 429: free-tier daily quota exceeded"}')


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_quota_error_is_not_replaced_with_generic_overload(self):
        test_settings = replace(
            ai_service.settings,
            gemini_api_key="test-key",
            gemini_model="gemini-3.8-flash",
            gemini_fallback_model="gemini-3.8-flash",
        )
        quota_error = ai_service.TransientProviderError("HTTP 429: quota exceeded", 59)
        with (
            patch.object(ai_service, "settings", test_settings),
            patch.object(ai_service, "_generate_gemini", side_effect=quota_error) as generate,
        ):
            with self.assertRaisesRegex(ai_service.TransientProviderError, "quota exceeded"):
                await ai_service.generate_text("short prompt")

        generate.assert_called_once_with("short prompt", None, "gemini-3.8-flash")

    async def test_transient_primary_failure_uses_configured_fallback(self):
        test_settings = replace(
            ai_service.settings,
            gemini_api_key="test-key",
            gemini_model="gemini-3.8-flash",
            gemini_fallback_model="gemini-3.6-flash",
        )

        def generate(prompt, response_mime_type, model=None):
            if model == "gemini-3.8-flash":
                raise ai_service.TransientProviderError("temporarily unavailable")
            return "Fallback answer"

        with (
            patch.object(ai_service, "settings", test_settings),
            patch.object(ai_service, "_generate_gemini", side_effect=generate) as mocked,
        ):
            result = await ai_service.generate_text("short prompt")

        self.assertEqual(result, "Fallback answer")
        self.assertEqual([call.args[2] for call in mocked.call_args_list], [
            "gemini-3.8-flash",
            "gemini-3.6-flash",
        ])


class QuizGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_quiz_generation_parses_provider_json_and_limits_question_count(self):
        questions = [
            {
                "question": f"Question {number}?",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "Because the notes say so.",
            }
            for number in range(1, 5)
        ]
        response = json.dumps({"questions": questions})
        with patch("quiz_module.generate_text", new=AsyncMock(return_value=response)) as generate:
            result = await generate_quiz(
                "These study notes are longer than forty characters for quiz generation.",
                3,
            )

        self.assertEqual(len(result["questions"]), 3)
        self.assertEqual(result["questions"][0]["question"], "Question 1?")
        generate.assert_awaited_once()
        self.assertEqual(generate.await_args.kwargs["response_mime_type"], "application/json")

    async def test_quiz_generation_parses_fenced_json(self):
        response = '''```json
{"questions":[{"question":"Q?","options":["A","B"],"answer":"A","explanation":"Reason."}]}
```'''
        with patch("quiz_module.generate_text", new=AsyncMock(return_value=response)):
            result = await generate_quiz(
                "These study notes are longer than forty characters for quiz generation.",
                3,
            )

        self.assertEqual(result["questions"][0]["answer"], "A")


if __name__ == "__main__":
    unittest.main()