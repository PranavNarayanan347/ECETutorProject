from fastapi import APIRouter

from services.api import deps
from services.api.schemas.request_response import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return deps._orchestrator.handle_chat(request)
