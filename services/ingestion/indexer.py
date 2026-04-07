from __future__ import annotations

from services.storage.models import Chunk


class Indexer:
    def __init__(self, postgres_repo, vector_repo, keyword_repo) -> None:
        self.postgres_repo = postgres_repo
        self.vector_repo = vector_repo
        self.keyword_repo = keyword_repo

    def index_chunks(self, chunks: list[Chunk]) -> None:
        self.postgres_repo.upsert_chunks(chunks)
        self.vector_repo.upsert_chunks(chunks)
        self.keyword_repo.upsert_chunks(chunks)
