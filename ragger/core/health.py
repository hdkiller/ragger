from ragger.core.workspaces import RAGWorkspaceManager


def get_health_status(manager: RAGWorkspaceManager) -> dict:
    return manager.get_health()
