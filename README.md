# ECE Tutor RAG MVP

Socratic, citation-grounded RAG backend for ECE tutoring.

## Quickstart

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -e .`
3. Copy env template:
   - `cp infra/env.example .env`
4. Start API:
   - `uvicorn services.api.main:app --reload`

## API Endpoints

- `POST /chat`
- `POST /ingest`
- `GET /sources/{doc_id}`
- `GET /health`

## Run Evaluation

- `python3 -m services.evals.run_eval`
- Prints retrieval, citation, Socratic compliance, and latency metrics.

## Project Layout

- `services/api`: FastAPI app and route handlers
- `services/tutor_engine`: Socratic policy and orchestration
- `services/retrieval`: Rewrite, retrieve, rerank, context-building logic
- `services/ingestion`: Parse, chunk, embed, and index ingestion pipeline
- `services/storage`: Postgres/vector/keyword/object-store repositories
- `services/evals`: Evaluation harness and metrics
- `infra`: local infra setup, migrations, and environment template
