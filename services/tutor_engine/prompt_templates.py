from __future__ import annotations

from services.api.schemas.request_response import ResponseType


SOCRATIC_SYSTEM = """\
You are a Socratic ECE tutor. Your goal is to help students understand \
electrical and computer engineering concepts through guided questioning.

Rules:
- Prefer asking ONE targeted question over giving a direct answer.
- Always show assumptions and include units in equations.
- Never fabricate equations, constants, or citations.
- Keep each response concise (under 200 words unless solving step-by-step).
- Reference the provided source context when it supports your response.
"""

QUESTION_INSTRUCTION = """\
Respond in Socratic style:
1. Ask a short diagnostic question to check the student's current understanding.
2. Follow with one guiding question that points toward the next reasoning step.
3. Cite relevant source material at the end.
Do NOT give the answer yet."""

HINT_INSTRUCTION = """\
The student needs a hint. Provide:
1. A conceptual hint (the key principle or law that applies).
2. A procedural nudge (what to write or calculate next).
3. End with "Would you like another hint, or want to try solving it?"
4. Cite relevant source material."""

SOLUTION_INSTRUCTION = """\
The student has requested a full solution. Provide:
1. A concise step-by-step solution with units.
2. A brief explanation of why this approach works.
3. One common mistake to watch out for.
4. Cite relevant source material."""


class PromptTemplates:
    def system_prompt(self, response_type: ResponseType) -> str:
        instruction = {
            ResponseType.question: QUESTION_INSTRUCTION,
            ResponseType.hint: HINT_INSTRUCTION,
            ResponseType.solution: SOLUTION_INSTRUCTION,
        }[response_type]
        return f"{SOCRATIC_SYSTEM}\n\n{instruction}"

    def user_message(self, query: str, context: str) -> str:
        return f"Student question: {query}\n\nSource context:\n{context}"

    def build_fallback(self, response_type: ResponseType, query: str, context: str) -> str:
        if response_type == ResponseType.question:
            return (
                "Check understanding:\n"
                f"- Which circuit law or concept do you think applies first to: '{query}'?\n\n"
                "Guiding question:\n"
                "- What known quantities and unknown quantity can you identify?\n\n"
                f"Sources:\n{context}"
            )
        if response_type == ResponseType.hint:
            return (
                "Hint:\n"
                "- Start by writing the governing equation for the node/loop.\n"
                "- Substitute given values with units before simplifying.\n\n"
                "Would you like another hint, or want to try solving it?\n\n"
                f"Sources:\n{context}"
            )
        return (
            "Concise solution:\n"
            "- Apply the governing relation step-by-step with units.\n"
            "- State the final quantity clearly.\n\n"
            "Why this works:\n"
            "- The approach follows from the cited principle and constraints.\n\n"
            f"Sources:\n{context}"
        )
