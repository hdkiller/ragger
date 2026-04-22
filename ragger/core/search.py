from __future__ import annotations

from typing import TYPE_CHECKING

from ragger.config import DEFAULT_MODEL_NAME, DEFAULT_PERSIST_DIRECTORY, DEFAULT_WORKSPACE

if TYPE_CHECKING:
    from ragger.core.workspaces import RAGWorkspaceManager


class RAGEngine:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIRECTORY,
        workspace: str = DEFAULT_WORKSPACE,
        manager: "RAGWorkspaceManager | None" = None,
    ):
        self.workspace = workspace
        if manager is None:
            from ragger.core.workspaces import RAGWorkspaceManager

            manager = RAGWorkspaceManager(
                persist_directory=persist_directory,
                model_name=model_name,
            )
        self.manager = manager
        self.model_name = self.manager.model_name
        self.embedding_model = self.manager.embedding_model
        self.persist_directory = self.manager.persist_directory

    def set_workspace(self, workspace: str) -> None:
        self.workspace = workspace

    def retrieve(self, question: str, k: int = 5, workspace: str | None = None):
        active_workspace = workspace or self.workspace
        return self.manager.retrieve_documents(workspace=active_workspace, query=question, k=k)

    def search(self, question: str, k: int = 5, workspace: str | None = None):
        active_workspace = workspace or self.workspace
        return self.manager.search_workspace(workspace=active_workspace, query=question, k=k)

    def stream_answer(self, question: str, docs):
        return self.manager.stream_answer(question=question, docs=docs)

    def get_stats(self, workspace: str | None = None):
        active_workspace = workspace or self.workspace
        stats = self.manager.get_workspace_stats(active_workspace)
        stats["workspace"] = active_workspace
        return stats

    def list_workspaces(self):
        return self.manager.list_workspaces()

    def list_workspace_files(self, workspace: str | None = None):
        active_workspace = workspace or self.workspace
        return self.manager.list_workspace_files(active_workspace)

    def get_health(self):
        return self.manager.get_health()

    def query(self, question: str, k: int = 5, workspace: str | None = None):
        active_workspace = workspace or self.workspace
        docs = self.retrieve(question=question, k=k, workspace=active_workspace)
        return self.stream_answer(question, docs)
