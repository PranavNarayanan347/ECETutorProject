from __future__ import annotations

from services.api.schemas.request_response import ResponseType


class PromptTemplates:
    def build(self, response_type: ResponseType, query: str, context: str) -> str:
        if response_type == ResponseType.question:
            return (
                "Check understanding:\n"
                f"- Which circuit law or concept do you think applies first to: '{query}'?\n\n"
                "Guiding question:\n"
                "- What known quantities and unknown quantity can you identify?\n\n"
                f"Relevant context:\n{context}"
            )
        if response_type == ResponseType.hint:
            return (
                "Hint:\n"
                "- Start by writing the governing equation for the node/loop.\n"
                "- Substitute given values with units before simplifying.\n\n"
                "If you want, ask for next hint.\n\n"
                f"Relevant context:\n{context}"
            )
        return (
            "Concise solution:\n"
            "- Apply the governing relation step-by-step with units.\n"
            "- State the final quantity clearly.\n\n"
            "Why this works:\n"
            "- The approach follows from the cited principle and constraints.\n\n"
            f"Relevant context:\n{context}"
        )
