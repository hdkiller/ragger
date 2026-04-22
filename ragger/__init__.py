from ragger.config import DEFAULT_WORKSPACE

__all__ = ["DEFAULT_WORKSPACE", "RAGEngine", "RAGWorkspaceManager"]


def __getattr__(name: str):
    if name == "DEFAULT_WORKSPACE":
        return DEFAULT_WORKSPACE
    if name == "RAGEngine":
        from ragger.core.search import RAGEngine

        return RAGEngine
    if name == "RAGWorkspaceManager":
        from ragger.core.workspaces import RAGWorkspaceManager

        return RAGWorkspaceManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
