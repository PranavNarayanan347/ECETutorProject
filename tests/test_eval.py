from services.api import deps
from services.evals.run_eval import run


def test_eval_runner_produces_metrics():
    metrics = run(
        orchestrator=deps._orchestrator,
        postgres_repo=deps._postgres_repo,
        vector_repo=deps._vector_repo,
        keyword_repo=deps._keyword_repo,
        dataset_path="services/evals/sample_dataset.json",
    )
    assert "recall_at_k" in metrics
    assert "citation_precision" in metrics
    assert "socratic_compliance" in metrics
    assert "avg_latency_ms" in metrics
    assert "p95_latency_ms" in metrics
