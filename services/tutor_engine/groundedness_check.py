from __future__ import annotations

from services.api.schemas.request_response import CitationModel


class GroundednessChecker:
    def check(self, content: str, citations: list[CitationModel]) -> tuple[float, str]:
        if not citations:
            return 0.25, "clarify"
        confidence = min(0.98, 0.5 + (0.1 * len(citations)))
        if len(content.strip()) < 20:
            confidence = min(confidence, 0.6)
        next_action = "offer_hint" if confidence >= 0.6 else "clarify"
        return confidence, next_action
