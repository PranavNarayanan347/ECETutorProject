from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from services.storage.models import ChatTurn, Chunk, Citation, Document


@dataclass
class InMemoryPostgresRepo:
    documents: dict[str, Document] = field(default_factory=dict)
    chunks: dict[str, Chunk] = field(default_factory=dict)
    sessions: set[str] = field(default_factory=set)
    chat_turns: dict[str, ChatTurn] = field(default_factory=dict)
    citations: dict[str, Citation] = field(default_factory=dict)

    def upsert_document(self, document: Document) -> None:
        self.documents[document.doc_id] = document

    def get_document(self, doc_id: str) -> Document | None:
        return self.documents.get(doc_id)

    def list_course_documents(self, course_id: str) -> list[Document]:
        return [doc for doc in self.documents.values() if doc.course_id == course_id]

    def upsert_chunks(self, chunks: Iterable[Chunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk

    def list_chunks_by_course(self, course_id: str) -> list[Chunk]:
        doc_ids = {d.doc_id for d in self.list_course_documents(course_id)}
        return [c for c in self.chunks.values() if c.doc_id in doc_ids]

    def save_chat_turn(self, turn: ChatTurn) -> None:
        self.sessions.add(turn.session_id)
        self.chat_turns[turn.turn_id] = turn

    def save_citations(self, citations: Iterable[Citation]) -> None:
        for citation in citations:
            self.citations[citation.citation_id] = citation
