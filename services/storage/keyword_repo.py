from __future__ import annotations

from dataclasses import dataclass, field

from services.storage.models import Chunk


class PgKeywordRepo:
    """Real Postgres full-text search."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _conn(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._dsn, row_factory=dict_row)

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        pass  # handled by postgres_repo / vector_repo upsert

    def search(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT chunk_id, doc_id, page, section, text, token_count, equation_flag,
                          ts_rank(tsv, plainto_tsquery('english', %s)) AS score
                   FROM chunks WHERE tsv @@ plainto_tsquery('english', %s)
                   ORDER BY score DESC LIMIT %s""",
                (query, query, top_k),
            ).fetchall()
        results: list[tuple[Chunk, float]] = []
        for r in rows:
            chunk = Chunk(
                chunk_id=r["chunk_id"], doc_id=r["doc_id"], page=r["page"],
                section=r["section"], text=r["text"], token_count=r["token_count"],
                equation_flag=r["equation_flag"], embedding=[],
            )
            results.append((chunk, float(r["score"])))
        return results


def _tokenize(text: str) -> set[str]:
    return {part.strip(".,:;!?()[]{}").lower() for part in text.split() if part.strip()}


@dataclass
class InMemoryKeywordRepo:
    chunks: dict[str, Chunk] = field(default_factory=dict)

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk

    def search(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        q_tokens = _tokenize(query)
        scored: list[tuple[Chunk, float]] = []
        for chunk in self.chunks.values():
            c_tokens = _tokenize(chunk.text)
            overlap = len(q_tokens.intersection(c_tokens))
            if overlap > 0:
                scored.append((chunk, float(overlap)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
