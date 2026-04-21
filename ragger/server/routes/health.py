from fastapi import APIRouter

from ragger.core.workspaces import RAGWorkspaceManager
from ragger.models import HealthStatus


def build_router(manager: RAGWorkspaceManager) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/health",
        response_model=HealthStatus,
        tags=["health"],
        summary="Check server and Ollama health",
    )
    def health():
        return manager.get_health()

    return router
