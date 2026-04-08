from __future__ import annotations

import logging

from services.api.config import get_settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._model = settings.embedding_model
        self._dim = settings.embedding_dim
        self._client = None

    def _get_client(self):
        if self._client is None and self._api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        if client is None:
            return self._fallback_embed(text)
        try:
            response = client.embeddings.create(
                model=self._model,
                input=text[:8000],
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.warning("OpenAI embedding failed (%s); using fallback.", exc)
            return self._fallback_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        if client is None:
            return [self._fallback_embed(t) for t in texts]
        try:
            response = client.embeddings.create(
                model=self._model,
                input=[t[:8000] for t in texts],
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning("OpenAI batch embedding failed (%s); using fallback.", exc)
            return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> list[float]:
        if not text:
            return [0.0] * self._dim
        values = [0.0] * self._dim
        for idx, ch in enumerate(text):
            values[idx % self._dim] += (ord(ch) % 31) / 31.0
        norm = sum(abs(v) for v in values) or 1.0
        return [v / norm for v in values]
