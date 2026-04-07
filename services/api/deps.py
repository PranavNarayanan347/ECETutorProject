from services.ingestion.ingest_runner import IngestionRunner
from services.storage.keyword_repo import InMemoryKeywordRepo
from services.storage.object_store import LocalObjectStore
from services.storage.postgres_repo import InMemoryPostgresRepo
from services.storage.vector_repo import InMemoryVectorRepo
from services.tutor_engine.orchestrator import RAGOrchestrator
from services.tutor_engine.session_manager import SessionManager

_postgres_repo = InMemoryPostgresRepo()
_vector_repo = InMemoryVectorRepo()
_keyword_repo = InMemoryKeywordRepo()
_object_store = LocalObjectStore()
_session_manager = SessionManager()

_orchestrator = RAGOrchestrator(
    session_manager=_session_manager,
    postgres_repo=_postgres_repo,
    vector_repo=_vector_repo,
    keyword_repo=_keyword_repo,
)

_ingestion_runner = IngestionRunner(
    postgres_repo=_postgres_repo,
    vector_repo=_vector_repo,
    keyword_repo=_keyword_repo,
    object_store=_object_store,
)
