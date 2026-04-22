from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
from chromadb import PersistentClient
from chromadb.errors import NotFoundError
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

from ragger.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MODEL_NAME,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_PERSIST_DIRECTORY,
    DEFAULT_WORKSPACE,
)
from ragger.core.ingest import CodebaseIngestor, IngestProgress


class RAGWorkspaceManager:
    def __init__(
        self,
        persist_directory: str = DEFAULT_PERSIST_DIRECTORY,
        model_name: str = DEFAULT_MODEL_NAME,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
    ):
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.ollama_base_url = ollama_base_url
        self.prompt = ChatPromptTemplate.from_template(
            """You are an expert software engineer assistant. Use the following retrieved context to answer the user's question.
If you don't know the answer, say that you don't know.
Keep the answer concise but technical.

Context:
{context}

Question: {question}

Answer:"""
        )

        self.persist_path = Path(self.persist_directory)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.persist_path / "ragger_workspaces.json"
        self.client = PersistentClient(path=str(self.persist_path))
        self.embeddings = OllamaEmbeddings(
            model=self.embedding_model, base_url=self.ollama_base_url
        )
        self.llm = ChatOllama(model=self.model_name, temperature=0, base_url=self.ollama_base_url)
        self.ingestor = CodebaseIngestor()

    def ingest_workspace(
        self,
        workspace: str,
        path: str,
        replace: bool = True,
        progress_callback: Callable[[IngestProgress], None] | None = None,
    ) -> dict[str, Any]:
        workspace = self._normalize_workspace(workspace)
        if replace:
            self._delete_collection(workspace)

        prepared = self.ingestor.prepare_documents(
            path=path,
            workspace=workspace,
            progress_callback=progress_callback,
        )
        vectorstore = self._get_vectorstore(workspace)
        if prepared.documents:
            vectorstore.add_documents(prepared.documents)

        chunk_count = self._collection_count(workspace)
        state = self._load_state()
        state[workspace] = {
            "workspace": workspace,
            "root_path": prepared.root_path,
            "collection_name": self._collection_name(workspace),
            "file_count": prepared.file_count,
            "chunk_count": chunk_count,
            "indexed_extensions": prepared.indexed_extensions,
            "indexed_files": self._build_file_manifest(prepared.documents),
            "last_indexed_at": self._timestamp(),
            "embedding_model": self.embedding_model,
            "model": self.model_name,
        }
        self._save_state(state)
        return state[workspace]

    def search_workspace(self, workspace: str, query: str, k: int = 5) -> list[dict[str, Any]]:
        workspace = self._normalize_workspace(workspace)
        self._ensure_workspace_exists(workspace)
        vectorstore = self._get_vectorstore(workspace)
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)
        return [self._serialize_search_hit(document, score) for document, score in docs_and_scores]

    def retrieve_documents(self, workspace: str, query: str, k: int = 5) -> list[Document]:
        workspace = self._normalize_workspace(workspace)
        self._ensure_workspace_exists(workspace)
        vectorstore = self._get_vectorstore(workspace)
        return vectorstore.similarity_search(query, k=k)

    def answer_workspace(self, workspace: str, question: str, k: int = 5):
        docs = self.retrieve_documents(workspace=workspace, query=question, k=k)
        return docs, self.stream_answer(question=question, docs=docs)

    def stream_answer(self, question: str, docs: list[Document]):
        chain = self.prompt | self.llm | StrOutputParser()
        return chain.stream({"context": self._format_docs(docs), "question": question})

    def list_workspaces(self) -> list[dict[str, Any]]:
        state = self._load_state()
        return [self.get_workspace_stats(workspace) for workspace in sorted(state)]

    def list_workspace_files(self, workspace: str) -> list[dict[str, Any]]:
        workspace = self._normalize_workspace(workspace)
        self._ensure_workspace_exists(workspace)
        state = self._load_state()
        stats = state[workspace]
        manifest = stats.get("indexed_files")
        if manifest:
            return manifest
        return self._build_file_manifest_from_root(stats.get("root_path", ""))

    def get_workspace_stats(self, workspace: str) -> dict[str, Any]:
        workspace = self._normalize_workspace(workspace)
        state = self._load_state()
        if workspace not in state:
            raise ValueError(f"Workspace does not exist: {workspace}")

        stats = dict(state[workspace])
        stats["chunk_count"] = self._collection_count(workspace)
        stats["embedding_model"] = self.embedding_model
        stats["model"] = self.model_name
        return stats

    def delete_workspace(self, workspace: str) -> dict[str, Any]:
        workspace = self._normalize_workspace(workspace)
        existed = workspace in self._load_state()
        self._delete_collection(workspace)
        state = self._load_state()
        state.pop(workspace, None)
        self._save_state(state)
        return {"workspace": workspace, "deleted": existed}

    def get_health(self) -> dict[str, Any]:
        ollama = {"reachable": False, "base_url": self.ollama_base_url, "models": []}
        try:
            response = httpx.get(f"{self.ollama_base_url}/api/tags", timeout=2.0)
            response.raise_for_status()
            payload = response.json()
            ollama["reachable"] = True
            ollama["models"] = [model.get("name", "") for model in payload.get("models", [])]
        except Exception as exc:  # pragma: no cover
            ollama["error"] = str(exc)

        return {
            "status": "ok",
            "persist_directory": self.persist_directory,
            "workspace_count": len(self._load_state()),
            "embedding_model": self.embedding_model,
            "model": self.model_name,
            "ollama": ollama,
        }

    def _serialize_search_hit(self, document: Document, score: float | None) -> dict[str, Any]:
        content = " ".join(document.page_content.split())
        return {
            "source": document.metadata.get("source", "unknown"),
            "relative_path": document.metadata.get("relative_path", "unknown"),
            "workspace": document.metadata.get("workspace", DEFAULT_WORKSPACE),
            "extension": document.metadata.get("extension", ""),
            "language": document.metadata.get("language", "text"),
            "score": score,
            "content_preview": content[:220],
            "content": document.page_content,
        }

    def _get_vectorstore(self, workspace: str) -> Chroma:
        return Chroma(
            collection_name=self._collection_name(workspace),
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def _delete_collection(self, workspace: str) -> None:
        try:
            self.client.delete_collection(self._collection_name(workspace))
        except (NotFoundError, ValueError):
            return

    def _collection_count(self, workspace: str) -> int:
        try:
            return self.client.get_collection(self._collection_name(workspace)).count()
        except (NotFoundError, ValueError):
            return 0

    def _collection_name(self, workspace: str) -> str:
        normalized = re.sub(r"[^a-z0-9_-]+", "_", workspace.lower()).strip("_") or DEFAULT_WORKSPACE
        return f"ragger_{normalized}"

    def _ensure_workspace_exists(self, workspace: str) -> None:
        if workspace not in self._load_state():
            raise ValueError(f"Workspace does not exist: {workspace}")

    @staticmethod
    def _normalize_workspace(workspace: str | None) -> str:
        return workspace.strip() if workspace else DEFAULT_WORKSPACE

    def _load_state(self) -> dict[str, dict[str, Any]]:
        if not self.metadata_path.exists():
            return {}
        return json.loads(self.metadata_path.read_text())

    def _save_state(self, state: dict[str, dict[str, Any]]) -> None:
        self.metadata_path.write_text(json.dumps(state, indent=2, sort_keys=True))

    @staticmethod
    def _format_docs(docs: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    def _build_file_manifest(self, documents: list[Document]) -> list[dict[str, Any]]:
        manifest: dict[str, dict[str, Any]] = {}
        for document in documents:
            relative_path = document.metadata.get("relative_path", "unknown")
            entry = manifest.setdefault(
                relative_path,
                {
                    "relative_path": relative_path,
                    "source": document.metadata.get("source", "unknown"),
                    "extension": document.metadata.get("extension", ""),
                    "language": document.metadata.get("language", "text"),
                    "chunk_count": 0,
                },
            )
            entry["chunk_count"] += 1
        return [manifest[path] for path in sorted(manifest)]

    def _build_file_manifest_from_root(self, root_path: str) -> list[dict[str, Any]]:
        source_path = Path(root_path).expanduser()
        if not source_path.exists():
            return []

        files = self.ingestor._collect_files(source_path.resolve())
        manifest: list[dict[str, Any]] = []
        for file_path in files:
            manifest.append(
                {
                    "relative_path": str(file_path.relative_to(source_path.resolve())),
                    "source": str(file_path.resolve()),
                    "extension": file_path.suffix.lower(),
                    "language": self.ingestor._get_language_name(file_path.suffix.lower()),
                    "chunk_count": None,
                }
            )
        return manifest

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
