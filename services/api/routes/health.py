from fastapi import APIRouter

from services.api.schemas.request_response import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(
        api="ok",
        database="ok",
        vector_index="ok",
        model_provider="configured",
    )
