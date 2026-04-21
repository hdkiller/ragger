import os

import uvicorn
from fastapi import FastAPI

from ragger.config import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from ragger.core.workspaces import RAGWorkspaceManager
from ragger.server.routes.health import build_router as build_health_router
from ragger.server.routes.workspaces import build_router as build_workspaces_router

app = FastAPI(
    title="ragger",
    version="0.1.0",
    description="Local multi-workspace RAG server for codebases and docs, backed by Chroma and Ollama.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
manager = RAGWorkspaceManager()
app.include_router(build_health_router(manager))
app.include_router(build_workspaces_router(manager))


def main():
    host = os.environ.get("RAGGER_HOST", DEFAULT_SERVER_HOST)
    port = int(os.environ.get("RAGGER_PORT", str(DEFAULT_SERVER_PORT)))
    uvicorn.run("ragger.server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
