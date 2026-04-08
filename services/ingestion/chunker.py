from __future__ import annotations

import re
from dataclasses import dataclass


SECTION_PATTERN = re.compile(
    r"^(?:"
    r"(?:chapter|section|part)\s+\d+"
    r"|(?:\d+\.)+\d*\s+"
    r"|[A-Z][A-Z\s]{4,}$"
    r")",
    re.IGNORECASE | re.MULTILINE,
)
EQUATION_SYMBOLS = {"=", "V", "I", "R", "Z", "C", "L", "omega", "\\int", "\\sum"}


@dataclass
class ChunkerConfig:
    target_tokens: int = 400
    max_tokens: int = 700
    overlap_tokens: int = 60


class Chunker:
    def __init__(self, config: ChunkerConfig | None = None) -> None:
        self.config = config or ChunkerConfig()

    def chunk_pages(self, pages: list[dict]) -> list[dict]:
        chunks: list[dict] = []
        for page in pages:
            text = page["text"].strip()
            if not text:
                continue
            sections = self._split_sections(text)
            for section_title, section_text in sections:
                chunks.extend(
                    self._window_chunk(section_text, page["page"], section_title)
                )
        return chunks

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        matches = list(SECTION_PATTERN.finditer(text))
        if not matches:
            return [("default", text)]
        sections: list[tuple[str, str]] = []
        if matches[0].start() > 0:
            sections.append(("preamble", text[: matches[0].start()]))
        for i, match in enumerate(matches):
            title = match.group().strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((title, text[start:end]))
        return sections

    def _window_chunk(self, text: str, page: int, section: str) -> list[dict]:
        words = text.split()
        if not words:
            return []
        target = self.config.target_tokens
        max_tok = self.config.max_tokens
        overlap = self.config.overlap_tokens
        chunks: list[dict] = []
        start = 0
        while start < len(words):
            end = min(len(words), start + max_tok)
            boundary = self._find_sentence_boundary(words, start + target, end)
            part_words = words[start:boundary]
            part_text = " ".join(part_words)
            chunks.append(
                {
                    "page": page,
                    "section": section,
                    "text": part_text,
                    "token_count": len(part_words),
                    "equation_flag": any(sym in part_text for sym in EQUATION_SYMBOLS),
                }
            )
            if boundary >= len(words):
                break
            start = max(boundary - overlap, start + 1)
        return chunks

    @staticmethod
    def _find_sentence_boundary(words: list[str], ideal: int, hard_max: int) -> int:
        best = min(ideal, hard_max)
        for i in range(min(ideal, len(words)), min(hard_max, len(words))):
            if words[i - 1].endswith((".", "?", "!", ":")):
                best = i
                break
        return min(best, len(words))
