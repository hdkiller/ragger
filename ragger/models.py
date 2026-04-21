from typing import Any

from pydantic import BaseModel, Field

from ragger.config import DEFAULT_WORKSPACE


class IndexRequest(BaseModel):
    workspace: str = Field(default=DEFAULT_WORKSPACE)
    path: str
    replace: bool = True


class SearchRequest(BaseModel):
    workspace: str = Field(default=DEFAULT_WORKSPACE)
    query: str
    k: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    source: str
    relative_path: str
    workspace: str
    extension: str
    language: str
    score: float | None = None
    content_preview: str
    content: str


class WorkspaceStats(BaseModel):
    workspace: str
    root_path: str
    collection_name: str
    file_count: int
    chunk_count: int
    indexed_extensions: list[str]
    last_indexed_at: str
    embedding_model: str
    model: str


class HealthStatus(BaseModel):
    status: str
    persist_directory: str
    workspace_count: int
    embedding_model: str
    model: str
    ollama: dict[str, Any]


class WorkspacesResponse(BaseModel):
    workspaces: list[WorkspaceStats]


class IndexResponse(WorkspaceStats):
    duration_seconds: float


class SearchResponse(BaseModel):
    workspace: str
    query: str
    results: list[SearchHit]


class DeleteWorkspaceResponse(BaseModel):
    workspace: str
    deleted: bool
