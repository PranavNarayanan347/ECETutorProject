from __future__ import annotations


class Embedder:
    def embed(self, text: str) -> list[float]:
        """
        Deterministic lightweight embedding stub for MVP scaffolding.
        """
        if not text:
            return [0.0] * 8
        values = [0.0] * 8
        for idx, ch in enumerate(text):
            values[idx % 8] += (ord(ch) % 31) / 31.0
        norm = sum(abs(v) for v in values) or 1.0
        return [v / norm for v in values]
