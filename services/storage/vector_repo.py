from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from services.storage.models import Chunk


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
