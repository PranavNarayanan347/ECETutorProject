from __future__ import annotations

import logging

from services.api.config import get_settings
from services.ingestion.ingest_runner import IngestionRunner
from services.tutor_engine.orchestrator import RAGOrchestrator
from services.tutor_engine.session_manager import SessionManager

logger = logging.getLogger(__name__)
settings = get_settings()

if settings.database_url:
    logger.info("Using real Postgres/pgvector storage backends.")
    from services.storage.keyword_repo import PgKeywordRepo
    from services.storage.object_store import FileSystemObjectStore
    from services.storage.postgres_repo import PostgresRepo
    from services.storage.vector_repo import PgVectorRepo

    postgres_repo = PostgresRepo(dsn=settings.database_url)
    vector_repo = PgVectorRepo(dsn=settings.database_url)
    keyword_repo = PgKeywordRepo(dsn=settings.database_url)
    object_store = FileSystemObjectStore(base_path=settings.object_store_path)
else:
    logger.info("No DATABASE_URL; falling back to in-memory storage.")
    from services.storage.keyword_repo import InMemoryKeywordRepo
    from services.storage.object_store import LocalObjectStore
    from services.storage.postgres_repo import InMemoryPostgresRepo
    from services.storage.vector_repo import InMemoryVectorRepo

    postgres_repo = InMemoryPostgresRepo()
    vector_repo = InMemoryVectorRepo()
    keyword_repo = InMemoryKeywordRepo()
    object_store = LocalObjectStore()

session_manager = SessionManager()

orchestrator = RAGOrchestrator(
    session_manager=session_manager,
    postgres_repo=postgres_repo,
    vector_repo=vector_repo,
    keyword_repo=keyword_repo,
)

ingestion_runner = IngestionRunner(
    postgres_repo=postgres_repo,
    vector_repo=vector_repo,
    keyword_repo=keyword_repo,
    object_store=object_store,
)
