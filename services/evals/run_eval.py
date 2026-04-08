from __future__ import annotations

import logging
import time

from services.api.schemas.request_response import ChatRequest
from services.evals.dataset_loader import load_dataset
from services.evals.metrics import citation_precision, retrieval_recall_at_k, socratic_compliance
from services.storage.models import Chunk, Document

logger = logging.getLogger(__name__)

SEED_CHUNKS = [
    {
        "chunk_id": "chk_manual_1",
        "section": "kcl",
        "text": (
            "Kirchhoff Current Law states the algebraic sum of currents at a node equals zero. "
            "KCL is derived from conservation of charge. It applies to any node in a circuit."
        ),
    },
    {
        "chunk_id": "chk_manual_2",
        "section": "kvl",
        "text": (
            "Kirchhoff Voltage Law states the algebraic sum of voltages around any closed loop equals zero. "
            "KVL is a consequence of conservation of energy."
        ),
    },
    {
        "chunk_id": "chk_manual_3",
        "section": "thevenin",
        "text": (
            "Thevenin's theorem: any linear two-terminal circuit can be replaced by a voltage source "
            "Vth in series with resistance Rth. Norton equivalent uses a current source in parallel."
        ),
    },
    {
        "chunk_id": "chk_manual_4",
        "section": "ohms_law",
        "text": (
            "Ohm's law: V = IR. Voltage across a resistor equals current times resistance. "
            "Power dissipated P = I^2 R = V^2 / R."
        ),
    },
    {
        "chunk_id": "chk_manual_5",
        "section": "ac_analysis",
        "text": (
            "In AC analysis, impedance Z = R + jX. For a capacitor Z_C = 1/(jwC), "
            "for an inductor Z_L = jwL. Phasor domain converts differential equations to algebra."
        ),
    },
    {
        "chunk_id": "chk_manual_6",
        "section": "op_amp",
        "text": (
            "An ideal operational amplifier has infinite input impedance, zero output impedance, "
            "and infinite open-loop gain. Inverting gain = -Rf/Rin. Non-inverting gain = 1 + Rf/Rin."
        ),
    },
    {
        "chunk_id": "chk_manual_7",
        "section": "signals",
        "text": (
            "The Nyquist sampling theorem states that a bandlimited signal can be perfectly reconstructed "
            "if sampled at a rate >= 2 times the highest frequency. Convolution in time domain is "
            "multiplication in frequency domain."
        ),
    },
    {
        "chunk_id": "chk_manual_8",
        "section": "digital",
        "text": (
            "Boolean algebra: A + A'B = A + B. Karnaugh maps simplify Boolean expressions. "
            "A D flip-flop captures input D on the rising clock edge. "
            "CMOS inverter uses complementary PMOS and NMOS transistors."
        ),
    },
]


def seed(orchestrator, postgres_repo, vector_repo, keyword_repo) -> None:
    doc = Document(
        doc_id="doc_manual",
        course_id="ece101",
        title="Circuit Fundamentals",
        source_uri="memory://doc_manual",
    )
    postgres_repo.upsert_document(doc)

    from services.ingestion.embedder import Embedder

    embedder = Embedder()
    chunks = []
    for spec in SEED_CHUNKS:
        embedding = embedder.embed(spec["text"])
        chunks.append(
            Chunk(
                chunk_id=spec["chunk_id"],
                doc_id="doc_manual",
                page=1,
                section=spec["section"],
                text=spec["text"],
                token_count=len(spec["text"].split()),
                equation_flag=True,
                embedding=embedding,
            )
        )
    postgres_repo.upsert_chunks(chunks)
    vector_repo.upsert_chunks(chunks)
    keyword_repo.upsert_chunks(chunks)


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
        all_seed_ids = [s["chunk_id"] for s in SEED_CHUNKS]
        recall = max(retrieval_recall_at_k(hit_ids, sid) for sid in all_seed_ids)
        recall_scores.append(recall)
        citation_scores.append(
            citation_precision([c.doc_id for c in response.citations], case.expected_doc_id)
        )
        socratic_scores.append(
            socratic_compliance(response.content, response.response_type.value)
        )

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
