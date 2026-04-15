# ECE Tutor RAG MVP

Socratic, citation-grounded RAG backend for ECE tutoring.

## Quickstart

1. Create a virtual environment and install:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
2. Copy env template and configure:
   ```bash
   cp infra/env.example .env
   # Edit .env: set OPENAI_API_KEY, DATABASE_URL, etc.
   ```
3. (Optional) Start Postgres with pgvector:
   ```bash
   docker compose -f infra/docker-compose.yml up -d
   ```
4. Start the API:
   ```bash
   uvicorn services.api.main:app --reload
   ```
5. Open the frontend at `http://localhost:8000`.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | None | Create account |
| POST | `/auth/login` | None | Get JWT token |
| POST | `/chat` | Optional | Send a chat message |
| POST | `/ingest` | Instructor/Admin | Upload a PDF for indexing |
| GET | `/sources/{doc_id}` | None | Get document metadata |
| GET | `/health` | None | Service health check |

## Run Tests

```bash
pytest -q
```

## Run Evaluation

```bash
python -m services.evals.run_eval
```

## CI Quality Gate

```bash
python -m scripts.run_ci_eval
```

Checks retrieval recall, citation precision, Socratic compliance, and latency against configured thresholds. Exits non-zero on failure.

## Project Layout

```
services/
  api/           FastAPI app, routes, schemas, auth, config
  tutor_engine/  Socratic policy, LLM client, prompt templates, orchestrator
  retrieval/     Query rewrite, hybrid retrieval, reranker, context builder
  ingestion/     PDF parser, chunker, embedder, ingestion runner
  storage/       Postgres, pgvector, keyword, object-store repositories
  evals/         Evaluation harness, metrics, benchmark dataset
frontend/        Chat UI (HTML + CSS + JS)
scripts/         CI and automation scripts
infra/           Docker Compose, migrations, env template
tests/           Pytest test suite
```

## Configuration

All settings are configured via environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | _(empty)_ | Postgres connection string; empty = in-memory mode |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key; empty = template-based responses |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `LLM_MODEL` | `gpt-4o-mini` | Chat completion model |
| `JWT_SECRET` | `change-me-in-production` | Secret for JWT signing |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `OBJECT_STORE_PATH` | `uploads` | Local path for uploaded PDFs |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic API key for circuit diagrams |
| `CIRCUIT_MODEL` | `claude-sonnet-4-20250514` | Claude model for SVG generation |

## Architecture

The system follows a layered design:

1. **Frontend** -- Chat UI with Socratic controls (hint/solution buttons), citation sidebar, confidence display
2. **API Layer** -- FastAPI with JWT auth, role-based access, CORS, structured error handling
3. **Tutor Engine** -- Socratic policy engine, LLM client, prompt templates, groundedness checker
4. **Retrieval Layer** -- Query rewriter, hybrid vector+keyword retrieval, cross-encoder reranker, context builder
5. **Knowledge Layer** -- PDF parser (PyMuPDF), semantic chunker, OpenAI embedder, triple-indexed storage
6. **Storage Layer** -- Postgres (metadata), pgvector (embeddings), full-text search (keywords), filesystem (PDFs)
