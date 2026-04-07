from __future__ import annotations

import time

from services.api.schemas.request_response import ChatRequest
from services.evals.dataset_loader import load_dataset
from services.evals.metrics import citation_precision, retrieval_recall_at_k, socratic_compliance
from services.storage.models import Chunk, Document


def seed(orchestrator, postgres_repo, vector_repo, keyword_repo) -> None:
    doc = Document(
        doc_id="doc_manual",
        course_id="ece101",
        title="Circuit Fundamentals",
        source_uri="memory://doc_manual",
    )
    postgres_repo.upsert_document(doc)
    chunk = Chunk(
        chunk_id="chk_manual_1",
        doc_id="doc_manual",
        page=1,
        section="kcl",
        text="Kirchhoff Current Law states algebraic sum of currents at a node equals zero.",
        token_count=13,
        equation_flag=True,
        embedding=[0.1] * 8,
    )
    postgres_repo.upsert_chunks([chunk])
    vector_repo.upsert_chunks([chunk])
    keyword_repo.upsert_chunks([chunk])


def run(orchestrator, postgres_repo, vector_repo, keyword_repo, dataset_path: str) -> dict:
    seed(orchestrator, postgres_repo, vector_repo, keyword_repo)
    dataset = load_dataset(dataset_path)

    recall_scores: list[float] = []
    citation_scores: list[float] = []
    socratic_scores: list[float] = []
    latencies_ms: list[float] = []

    for case in dataset:
        started = time.perf_counter()
        response = orchestrator.handle_chat(
            ChatRequest(
                session_id=f"eval_{case.id}",
                course_id="ece101",
                message=case.query,
                allow_full_solution=False,
            )
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies_ms.append(elapsed_ms)
        hit_ids = response.retrieval_trace.selected_chunk_ids
        recall_scores.append(retrieval_recall_at_k(hit_ids, "chk_manual_1"))
        citation_scores.append(citation_precision([c.doc_id for c in response.citations], case.expected_doc_id))
        socratic_scores.append(socratic_compliance(response.content, response.response_type.value))

    n = max(len(dataset), 1)
    sorted_latencies = sorted(latencies_ms)
    p95_idx = max(0, int(0.95 * len(sorted_latencies)) - 1)
    return {
        "recall_at_k": sum(recall_scores) / n,
        "citation_precision": sum(citation_scores) / n,
        "socratic_compliance": sum(socratic_scores) / n,
        "avg_latency_ms": sum(latencies_ms) / n,
        "p95_latency_ms": sorted_latencies[p95_idx] if sorted_latencies else 0.0,
        "case_count": n,
    }


if __name__ == "__main__":
    from services.api import deps

    results = run(
        orchestrator=deps._orchestrator,
        postgres_repo=deps._postgres_repo,
        vector_repo=deps._vector_repo,
        keyword_repo=deps._keyword_repo,
        dataset_path="services/evals/sample_dataset.json",
    )
    for key, value in results.items():
        print(f"{key}: {value}")
