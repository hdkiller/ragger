import time

from fastapi import APIRouter, HTTPException

from ragger.core.workspaces import RAGWorkspaceManager
from ragger.models import (
    DeleteWorkspaceResponse,
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    WorkspaceStats,
    WorkspacesResponse,
)


def build_router(manager: RAGWorkspaceManager) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/workspaces",
        response_model=WorkspacesResponse,
        tags=["workspaces"],
        summary="List indexed workspaces",
    )
    def list_workspaces():
        return {"workspaces": manager.list_workspaces()}

    @router.get(
        "/workspaces/{workspace}/stats",
        response_model=WorkspaceStats,
        tags=["workspaces"],
        summary="Get workspace stats",
    )
    def workspace_stats(workspace: str):
        try:
            return manager.get_workspace_stats(workspace)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/workspaces/{workspace}/status",
        response_model=WorkspaceStats,
        tags=["workspaces"],
        summary="Get workspace status",
    )
    def workspace_status(workspace: str):
        try:
            return manager.get_workspace_stats(workspace)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(
        "/workspaces/index",
        response_model=IndexResponse,
        tags=["workspaces"],
        summary="Index or reindex a workspace",
    )
    def index_workspace(request: IndexRequest):
        started = time.perf_counter()
        try:
            stats = manager.ingest_workspace(
                workspace=request.workspace,
                path=request.path,
                replace=request.replace,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {**stats, "duration_seconds": round(time.perf_counter() - started, 3)}

    @router.post(
        "/workspaces/search",
        response_model=SearchResponse,
        tags=["workspaces"],
        summary="Search an indexed workspace",
    )
    def search_workspace(request: SearchRequest):
        try:
            results = manager.search_workspace(
                workspace=request.workspace,
                query=request.query,
                k=request.k,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"workspace": request.workspace, "query": request.query, "results": results}

    @router.delete(
        "/workspaces/{workspace}",
        response_model=DeleteWorkspaceResponse,
        tags=["workspaces"],
        summary="Delete an indexed workspace",
    )
    def delete_workspace(workspace: str):
        return manager.delete_workspace(workspace)

    return router
