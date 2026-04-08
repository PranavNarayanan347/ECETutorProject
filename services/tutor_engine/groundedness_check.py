from __future__ import annotations

import logging

from services.api.schemas.request_response import CitationModel
from services.tutor_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class GroundednessChecker:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client

    def check(
        self, content: str, context: str, citations: list[CitationModel],
    ) -> tuple[float, str]:
        if not citations:
            return 0.25, "clarify"

        heuristic = min(0.98, 0.5 + (0.1 * len(citations)))
        if len(content.strip()) < 20:
            heuristic = min(heuristic, 0.6)

        if self._llm and self._llm.available:
            try:
                llm_score = self._llm.judge_groundedness(content, context)
                confidence = (heuristic + llm_score) / 2.0
            except Exception as exc:
                logger.warning("LLM groundedness check failed: %s", exc)
                confidence = heuristic
        else:
            confidence = heuristic

        if confidence >= 0.7:
            next_action = "offer_hint"
        elif confidence >= 0.5:
            next_action = "offer_hint"
        else:
            next_action = "clarify"
        return round(confidence, 3), next_action
