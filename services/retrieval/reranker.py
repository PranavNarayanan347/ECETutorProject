from __future__ import annotations

from services.storage.models import Chunk


class Reranker:
    def rerank(self, query: str, candidates: list[tuple[Chunk, float]], top_k: int = 6) -> list[tuple[Chunk, float]]:
        boost_terms = {"equation", "derive", "solve", "current", "voltage", "resistance"}
        reranked: list[tuple[Chunk, float]] = []
        for chunk, score in candidates:
            text = chunk.text.lower()
            term_boost = sum(0.05 for term in boost_terms if term in text)
            equation_boost = 0.1 if chunk.equation_flag else 0.0
            reranked.append((chunk, score + term_boost + equation_boost))
        reranked.sort(key=lambda item: item[1], reverse=True)
        return reranked[:top_k]
