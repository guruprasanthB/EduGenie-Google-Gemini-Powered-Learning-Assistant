from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ai_service import TransientProviderError
from config import settings
from schemas import (
    ExplainRequest,
    QARequest,
    QuizRequest,
    SummaryRequest,
    LearningPathRequest,
    ErrorResponse,
)
from qna import answer_question
from explanation_module import explain_concept
from quiz_module import generate_quiz
from summary_module import summarize_text
from learning_path import get_learning_recommendations


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="EduGenie - Gemini Powered Learning Assistant",
    description=(
        "AI educational assistant providing Q&A, "
        "concept explanations, quizzes, summaries, "
        "and personalized learning paths."
    ),
    version="1.0.0",
)


# Static files
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# Jinja templates
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "app_name": settings.app_name,
        },
    )


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "app": settings.app_name,
        "gemini_configured": bool(settings.gemini_api_key),
        "model": settings.gemini_model,
    }


# -----------------------------
# Question Answering
# -----------------------------

@app.post("/qa")
async def qa(payload: QARequest):

    result = await answer_question(
        payload.question
    )

    return {
        "success": True,
        "result": result,
    }


# -----------------------------
# Concept Explanation
# -----------------------------

@app.post("/explain")
async def explain(payload: ExplainRequest):

    result = await explain_concept(
        payload.topic,
        payload.level,
    )

    return {
        "success": True,
        "result": result,
    }


# -----------------------------
# Quiz Generation
# -----------------------------

@app.post("/quiz")
async def quiz(payload: QuizRequest):

    quiz = await generate_quiz(
        payload.text,
        payload.question_count,
    )

    return {
        "success": True,
        "quiz": quiz,
    }


# -----------------------------
# Summarization
# -----------------------------

@app.post("/summarize")
async def summarize(payload: SummaryRequest):

    result = await summarize_text(
        payload.text,
        payload.style,
    )

    return {
        "success": True,
        "result": result,
    }


# -----------------------------
# Learning Path
# -----------------------------

@app.post("/learn/recommendations")
async def learning_recommendations(
    payload: LearningPathRequest,
):

    result = await get_learning_recommendations(
        payload.topic,
        payload.level,
        payload.duration,
    )

    return {
        "success": True,
        "result": result,
    }


# -----------------------------
# Error Handler
# -----------------------------

@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
):

    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error=str(exc)).model_dump(),
    )


@app.exception_handler(TransientProviderError)
async def transient_provider_error_handler(
    request: Request,
    exc: TransientProviderError,
):
    headers = {}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(max(0, int(exc.retry_after)))

    return JSONResponse(
        status_code=503,
        content=ErrorResponse(error=str(exc)).model_dump(),
        headers=headers,
    )