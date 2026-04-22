__all__ = ["CodebaseIngestor", "IngestPreparation", "RAGEngine", "RAGWorkspaceManager"]


def __getattr__(name: str):
    if name in {"CodebaseIngestor", "IngestPreparation"}:
        from ragger.core.ingest import CodebaseIngestor, IngestPreparation

        return {"CodebaseIngestor": CodebaseIngestor, "IngestPreparation": IngestPreparation}[name]
    if name == "RAGEngine":
        from ragger.core.search import RAGEngine

        return RAGEngine
    if name == "RAGWorkspaceManager":
        from ragger.core.workspaces import RAGWorkspaceManager

        return RAGWorkspaceManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
