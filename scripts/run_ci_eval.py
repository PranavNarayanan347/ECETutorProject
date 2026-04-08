"""
CI evaluation gate.

Usage:
    python -m scripts.run_ci_eval

Exits with code 1 if any quality threshold is not met.
"""
from __future__ import annotations

import json
import sys
import time

from services.api import deps
from services.evals.run_eval import run

THRESHOLDS = {
    "recall_at_k": 0.80,
    "citation_precision": 0.90,
    "socratic_compliance": 0.90,
    "p95_latency_ms": 6000.0,
}


def main() -> None:
    print("=" * 60)
    print("ECE Tutor RAG -- CI Evaluation Gate")
    print("=" * 60)

    start = time.time()
    results = run(
        orchestrator=deps._orchestrator,
        postgres_repo=deps._postgres_repo,
        vector_repo=deps._vector_repo,
        keyword_repo=deps._keyword_repo,
        dataset_path="services/evals/sample_dataset.json",
    )
    elapsed = time.time() - start

    print(f"\nResults ({results['case_count']} cases, {elapsed:.1f}s):")
    print(json.dumps(results, indent=2))

    failures: list[str] = []
    for metric, threshold in THRESHOLDS.items():
        value = results.get(metric, 0.0)
        if metric == "p95_latency_ms":
            passed = value <= threshold
        else:
            passed = value >= threshold
        status = "PASS" if passed else "FAIL"
        print(f"  {metric}: {value:.3f} (threshold {threshold}) [{status}]")
        if not passed:
            failures.append(metric)

    print()
    if failures:
        print(f"FAILED gates: {', '.join(failures)}")
        sys.exit(1)
    else:
        print("All quality gates PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
