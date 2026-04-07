from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ResponseType(str, Enum):
    question = "question"
    hint = "hint"
    solution = "solution"


class CitationModel(BaseModel):
    chunk_id: str
    doc_id: str
    page: int
    snippet: str


class RetrievalTraceModel(BaseModel):
    query: str
    rewrite: str | None = None
    candidate_count: int = 0
    selected_chunk_ids: list[str] = Field(default_factory=list)
    latency_ms: int = 0


class ChatRequest(BaseModel):
    session_id: str
    course_id: str
    message: str = Field(min_length=1)
    student_intent: str | None = None
    allow_full_solution: bool = False


class ChatResponse(BaseModel):
    response_type: ResponseType
    content: str
    citations: list[CitationModel] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    next_action: Literal["ask_next_step", "offer_hint", "offer_solution", "clarify"]
    retrieval_trace: RetrievalTraceModel


class IngestResponse(BaseModel):
    document_id: str
    status: Literal["queued", "processing", "complete", "failed"]
    chunk_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class SourceResponse(BaseModel):
    doc_id: str
    course_id: str
    title: str
    source_uri: str
    version: int
    status: str


class HealthStatus(BaseModel):
    api: str = "ok"
    database: str = "unknown"
    vector_index: str = "unknown"
    model_provider: str = "unknown"
