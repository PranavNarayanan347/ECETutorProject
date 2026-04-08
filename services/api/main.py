import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from services.api.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ECE Tutor RAG MVP", version="0.2.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from services.api.routes.auth import router as auth_router  # noqa: E402
from services.api.routes.chat import router as chat_router  # noqa: E402
from services.api.routes.health import router as health_router  # noqa: E402
from services.api.routes.ingest import router as ingest_router  # noqa: E402
from services.api.routes.sources import router as sources_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(sources_router)

try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except Exception:
    logger.info("Frontend directory not found; static serving disabled.")
