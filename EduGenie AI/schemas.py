from pydantic import BaseModel, Field


class QARequest(BaseModel):
    question: str = Field(min_length=3, max_length=40000)


class ExplainRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=500)
    level: str = Field(default="beginner", max_length=40)


class QuizRequest(BaseModel):
    text: str = Field(min_length=40, max_length=40000)
    question_count: int = Field(default=5, ge=3, le=8)


class SummaryRequest(BaseModel):
    text: str = Field(min_length=40, max_length=40000)
    style: str = Field(default="concise", max_length=40)


class LearningPathRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=500)
    level: str = Field(default="beginner", max_length=40)
    duration: int = Field(default=4, ge=1, le=24)


class ErrorResponse(BaseModel):
    error: str