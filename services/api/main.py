from fastapi import FastAPI

from services.api.routes.chat import router as chat_router
from services.api.routes.health import router as health_router
from services.api.routes.ingest import router as ingest_router
from services.api.routes.sources import router as sources_router

app = FastAPI(title="ECE Tutor RAG MVP", version="0.1.0")
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(sources_router)
