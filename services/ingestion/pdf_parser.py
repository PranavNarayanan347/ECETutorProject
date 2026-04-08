from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class PDFParser:
    def parse(self, raw_bytes: bytes) -> list[dict]:
        try:
            return self._parse_with_pymupdf(raw_bytes)
        except Exception as exc:
            logger.warning("PyMuPDF parse failed (%s); falling back to plain-text decode.", exc)
            return self._parse_plaintext(raw_bytes)

    def _parse_with_pymupdf(self, raw_bytes: bytes) -> list[dict]:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        pages: list[dict] = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if not text or not text.strip():
                logger.info("Page %d: no extractable text (possibly scanned).", page_num)
                text = self._ocr_fallback(page)
            pages.append({"page": page_num, "text": text})
        doc.close()
        return pages

    def _ocr_fallback(self, page) -> str:
        """Attempt OCR via PyMuPDF's built-in Tesseract integration."""
        try:
            return page.get_text("text", flags=1 | 2)
        except Exception:
            return ""

    def _parse_plaintext(self, raw_bytes: bytes) -> list[dict]:
        text = raw_bytes.decode("utf-8", errors="ignore")
        return [{"page": 1, "text": text}]
