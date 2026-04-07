from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EvalCase:
    id: str
    query: str
    expected_doc_id: str
    expected_page: int
    expected_response_type: str


def load_dataset(path: str) -> list[EvalCase]:
    raw = json.loads(Path(path).read_text())
    return [EvalCase(**item) for item in raw]
