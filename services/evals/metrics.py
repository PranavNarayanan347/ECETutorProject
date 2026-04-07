from __future__ import annotations


def retrieval_recall_at_k(hits: list[str], expected: str) -> float:
    return 1.0 if expected in hits else 0.0


def citation_precision(citation_doc_ids: list[str], expected_doc_id: str) -> float:
    if not citation_doc_ids:
        return 0.0
    correct = sum(1 for doc_id in citation_doc_ids if doc_id == expected_doc_id)
    return correct / len(citation_doc_ids)


def socratic_compliance(content: str, response_type: str) -> float:
    lowered = content.lower()
    if response_type == "question" and "guiding question" in lowered:
        return 1.0
    if response_type == "hint" and "hint" in lowered:
        return 1.0
    if response_type == "solution" and "concise solution" in lowered:
        return 1.0
    return 0.0
