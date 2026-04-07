from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChunkerConfig:
    chunk_size: int = 500
    overlap: int = 80


class Chunker:
    def __init__(self, config: ChunkerConfig | None = None) -> None:
        self.config = config or ChunkerConfig()

    def chunk_pages(self, pages: list[dict]) -> list[dict]:
        chunks: list[dict] = []
        for page in pages:
            text = page["text"].strip()
            if not text:
                continue
            start = 0
            while start < len(text):
                end = min(len(text), start + self.config.chunk_size)
                part = text[start:end]
                chunks.append(
                    {
                        "page": page["page"],
                        "section": "default",
                        "text": part,
                        "token_count": max(1, len(part.split())),
                        "equation_flag": any(sym in part for sym in ["=", "V", "I", "R"]),
                    }
                )
                if end >= len(text):
                    break
                start = max(end - self.config.overlap, start + 1)
        return chunks
