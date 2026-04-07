from fastapi import APIRouter, File, Form, UploadFile

from services.api import deps
from services.api.schemas.request_response import IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse)
async def ingest(
    course_id: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    module: str | None = Form(default=None),
    topic: str | None = Form(default=None),
) -> IngestResponse:
    return await deps._ingestion_runner.run(
        course_id=course_id,
        title=title,
        file=file,
        module=module,
        topic=topic,
    )
