from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from services.storage.models import ChatTurn, Chunk, Citation, Document


class PostgresRepo:
    """Real Postgres-backed repository."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _conn(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._dsn, row_factory=dict_row)

    def upsert_document(self, document: Document) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO documents (doc_id, course_id, title, source_uri, version, status)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (doc_id) DO UPDATE SET title=EXCLUDED.title, status=EXCLUDED.status""",
                (document.doc_id, document.course_id, document.title,
                 document.source_uri, document.version, document.status),
            )
            conn.commit()

    def get_document(self, doc_id: str) -> Document | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT doc_id, course_id, title, source_uri, version, status FROM documents WHERE doc_id=%s",
                (doc_id,),
            ).fetchone()
        if row is None:
            return None
        return Document(
            doc_id=row["doc_id"], course_id=row["course_id"], title=row["title"],
            source_uri=row["source_uri"], version=row["version"], status=row["status"],
        )

    def list_course_documents(self, course_id: str) -> list[Document]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT doc_id, course_id, title, source_uri, version, status FROM documents WHERE course_id=%s",
                (course_id,),
            ).fetchall()
        return [
            Document(doc_id=r["doc_id"], course_id=r["course_id"], title=r["title"],
                     source_uri=r["source_uri"], version=r["version"], status=r["status"])
            for r in rows
        ]

    def upsert_chunks(self, chunks: Iterable[Chunk]) -> None:
        with self._conn() as conn:
            for c in chunks:
                conn.execute(
                    """INSERT INTO chunks (chunk_id, doc_id, page, section, text, token_count, equation_flag, embedding, tsv)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, to_tsvector('english', %s))
                       ON CONFLICT (chunk_id) DO NOTHING""",
                    (c.chunk_id, c.doc_id, c.page, c.section, c.text,
                     c.token_count, c.equation_flag, str(c.embedding), c.text),
                )
            conn.commit()

    def list_chunks_by_course(self, course_id: str) -> list[Chunk]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT c.chunk_id, c.doc_id, c.page, c.section, c.text, c.token_count, c.equation_flag
                   FROM chunks c JOIN documents d ON c.doc_id=d.doc_id WHERE d.course_id=%s""",
                (course_id,),
            ).fetchall()
        return [
            Chunk(chunk_id=r["chunk_id"], doc_id=r["doc_id"], page=r["page"],
                  section=r["section"], text=r["text"], token_count=r["token_count"],
                  equation_flag=r["equation_flag"], embedding=[])
            for r in rows
        ]

    def save_chat_turn(self, turn: ChatTurn) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO sessions (session_id, course_id) VALUES (%s, 'default')
                   ON CONFLICT (session_id) DO UPDATE SET updated_at=NOW()""",
                (turn.session_id,),
            )
            conn.execute(
                """INSERT INTO chat_turns (turn_id, session_id, role, content, response_type, confidence)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (turn.turn_id, turn.session_id, turn.role, turn.content,
                 turn.response_type, turn.confidence),
            )
            conn.commit()

    def save_citations(self, citations: Iterable[Citation]) -> None:
        with self._conn() as conn:
            for c in citations:
                conn.execute(
                    """INSERT INTO citations (citation_id, turn_id, chunk_id, doc_id, page, snippet)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (c.citation_id, c.turn_id, c.chunk_id, c.doc_id, c.page, c.snippet),
                )
            conn.commit()


@dataclass
class InMemoryPostgresRepo:
    """In-memory implementation for tests and local dev without a database."""

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
