from __future__ import annotations

from services.ingestion.embedder import Embedder
from services.storage.models import Chunk


class HybridRetriever:
    def __init__(self, vector_repo, keyword_repo) -> None:
        self.vector_repo = vector_repo
        self.keyword_repo = keyword_repo
        self.embedder = Embedder()

    def retrieve(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        q_embedding = self.embedder.embed(query)
        vector_hits = self.vector_repo.search(q_embedding, top_k=top_k)
        keyword_hits = self.keyword_repo.search(query, top_k=top_k)

        fused: dict[str, tuple[Chunk, float]] = {}
        for rank, (chunk, score) in enumerate(vector_hits, start=1):
            fused[chunk.chunk_id] = (chunk, score + (1.0 / (50 + rank)))
        for rank, (chunk, score) in enumerate(keyword_hits, start=1):
            bonus = score + (1.0 / (50 + rank))
            if chunk.chunk_id in fused:
                fused[chunk.chunk_id] = (chunk, fused[chunk.chunk_id][1] + bonus)
            else:
                fused[chunk.chunk_id] = (chunk, bonus)

        ranked = list(fused.values())
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:top_k]
