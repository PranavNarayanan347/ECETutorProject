from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Document:
    doc_id: str
    course_id: str
    title: str
    source_uri: str
    version: int = 1
    ingested_at: datetime = field(default_factory=utc_now)
    status: str = "complete"

    def model_dump(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "course_id": self.course_id,
            "title": self.title,
            "source_uri": self.source_uri,
            "version": self.version,
            "status": self.status,
        }


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    page: int
    section: str
    text: str
    token_count: int
    equation_flag: bool
    embedding: list[float]


@dataclass
class ChatTurn:
    turn_id: str
    session_id: str
    role: str
    content: str
    response_type: str
    confidence: float
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Citation:
    citation_id: str
    turn_id: str
    chunk_id: str
    doc_id: str
    page: int
    snippet: str
