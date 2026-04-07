from __future__ import annotations


class PDFParser:
    def parse(self, raw_bytes: bytes) -> list[dict]:
        """
        MVP parser: decodes text content as a single page.
        Replace with a PDF library in Phase 2 hardening.
        """
        text = raw_bytes.decode("utf-8", errors="ignore")
        return [{"page": 1, "text": text}]
