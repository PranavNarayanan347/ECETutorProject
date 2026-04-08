from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from services.storage.models import Chunk


class PgVectorRepo:
    """Real pgvector-backed vector search."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _conn(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._dsn, row_factory=dict_row)

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        with self._conn() as conn:
            for c in chunks:
                conn.execute(
                    """INSERT INTO chunks (chunk_id, doc_id, page, section, text, token_count, equation_flag, embedding, tsv)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, to_tsvector('english', %s))
                       ON CONFLICT (chunk_id) DO UPDATE SET embedding=EXCLUDED.embedding""",
                    (c.chunk_id, c.doc_id, c.page, c.section, c.text,
                     c.token_count, c.equation_flag, str(c.embedding), c.text),
                )
            conn.commit()

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[tuple[Chunk, float]]:
        vec_str = str(query_embedding)
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT chunk_id, doc_id, page, section, text, token_count, equation_flag,
                          1 - (embedding <=> %s::vector) AS score
                   FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s""",
                (vec_str, vec_str, top_k),
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


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a)) or 1.0
    norm_b = sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


@dataclass
class InMemoryVectorRepo:
    vectors: dict[str, Chunk] = field(default_factory=dict)

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self.vectors[chunk.chunk_id] = chunk

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[tuple[Chunk, float]]:
        scored = [
            (chunk, _cosine(query_embedding, chunk.embedding))
            for chunk in self.vectors.values()
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
