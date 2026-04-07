from fastapi import APIRouter, HTTPException

from services.api import deps
from services.api.schemas.request_response import SourceResponse

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/{doc_id}", response_model=SourceResponse)
def get_source(doc_id: str) -> SourceResponse:
    doc = deps._postgres_repo.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return SourceResponse(**doc.model_dump())
