from typing import Annotated

from fastapi import APIRouter, Depends

from services.api import deps
from services.api.auth import get_current_user
from services.api.schemas.request_response import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: Annotated[dict | None, Depends(get_current_user)] = None,
) -> ChatResponse:
    return deps.orchestrator.handle_chat(request)
