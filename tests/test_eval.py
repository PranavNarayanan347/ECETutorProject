from services.api import deps
from services.evals.run_eval import run


def test_eval_runner_produces_metrics():
    metrics = run(
        orchestrator=deps.orchestrator,
        postgres_repo=deps.postgres_repo,
        vector_repo=deps.vector_repo,
        keyword_repo=deps.keyword_repo,
        dataset_path="services/evals/sample_dataset.json",
    )
    assert "recall_at_k" in metrics
    assert "citation_precision" in metrics
    assert "socratic_compliance" in metrics
    assert "avg_latency_ms" in metrics
    assert "p95_latency_ms" in metrics
    assert metrics["case_count"] == 50
