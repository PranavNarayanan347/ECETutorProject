from __future__ import annotations

from dataclasses import dataclass, field

from services.storage.models import Chunk


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
