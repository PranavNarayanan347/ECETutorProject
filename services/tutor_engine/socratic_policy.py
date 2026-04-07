from __future__ import annotations

from services.api.schemas.request_response import ResponseType


class SocraticPolicyEngine:
    def choose_response_type(
        self,
        message: str,
        allow_full_solution: bool,
        hint_level: int,
    ) -> ResponseType:
        lowered = message.lower()
        wants_solution = any(term in lowered for term in ["full solution", "just answer", "final answer"])
        if allow_full_solution or (wants_solution and hint_level >= 1):
            return ResponseType.solution
        if hint_level > 0 or "hint" in lowered:
            return ResponseType.hint
        return ResponseType.question
