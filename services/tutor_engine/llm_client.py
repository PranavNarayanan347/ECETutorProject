from __future__ import annotations

import logging

from services.api.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._model = settings.llm_model
        self._client = None

    def _get_client(self):
        if self._client is None and self._api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def generate(self, system_prompt: str, user_message: str) -> str:
        client = self._get_client()
        if client is None:
            raise RuntimeError("No OpenAI API key configured.")
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content or ""

    def judge_groundedness(self, answer: str, context: str) -> float:
        client = self._get_client()
        if client is None:
            return 0.7
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a grading assistant. Given an ANSWER and SOURCE CONTEXT, "
                            "rate how well the answer is supported by the context on a scale "
                            "from 0.0 (no support) to 1.0 (fully supported). "
                            "Reply with ONLY a decimal number."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"ANSWER:\n{answer}\n\nSOURCE CONTEXT:\n{context}",
                    },
                ],
                temperature=0.0,
                max_tokens=10,
            )
            text = (response.choices[0].message.content or "0.5").strip()
            return max(0.0, min(1.0, float(text)))
        except Exception as exc:
            logger.warning("Groundedness judge failed (%s); defaulting to 0.7.", exc)
            return 0.7
