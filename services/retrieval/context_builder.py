from __future__ import annotations

from services.api.schemas.request_response import CitationModel
from services.storage.models import Chunk


class ContextBuilder:
    def build(
        self,
        selected: list[tuple[Chunk, float]],
        max_chars: int = 2200,
    ) -> tuple[str, list[CitationModel], list[str]]:
        context_parts: list[str] = []
        citations: list[CitationModel] = []
        selected_ids: list[str] = []
        used = 0

        for chunk, _score in selected:
            snippet = chunk.text.strip()
            addition = f"[{chunk.doc_id} p{chunk.page}] {snippet}"
            if used + len(addition) > max_chars:
                break
            context_parts.append(addition)
            citations.append(
                CitationModel(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    page=chunk.page,
                    snippet=snippet[:180],
                )
            )
            selected_ids.append(chunk.chunk_id)
            used += len(addition)

        return "\n\n".join(context_parts), citations, selected_ids
