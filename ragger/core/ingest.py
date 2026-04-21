import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


CODE_LANGUAGE_BY_EXTENSION: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".html": Language.HTML,
    ".md": Language.MARKDOWN,
}

SUPPORTED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".scss",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    ".cache",
    ".chroma_db",
}

EXCLUDED_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "Cargo.lock",
    "poetry.lock",
}

EXCLUDED_SUFFIXES = {
    ".map",
    ".min.js",
    ".min.css",
}

MAX_FILE_SIZE_BYTES = 1_000_000


@dataclass
class IngestPreparation:
    documents: list[Document]
    file_count: int
    chunk_count: int
    indexed_extensions: list[str]
    root_path: str


class CodebaseIngestor:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def prepare_documents(self, path: str, workspace: str) -> IngestPreparation:
        source_path = Path(path).expanduser().resolve()
        if not source_path.exists():
            raise ValueError(f"Path does not exist: {path}")

        root_path = source_path.parent if source_path.is_file() else source_path
        files = self._collect_files(source_path)
        if not files:
            raise ValueError(f"No supported files found in: {source_path}")

        all_chunks: list[Document] = []
        indexed_extensions: set[str] = set()

        for file_path in files:
            indexed_extensions.add(file_path.suffix.lower())
            chunks = self._chunk_file(file_path=file_path, root_path=root_path, workspace=workspace)
            all_chunks.extend(chunks)

        return IngestPreparation(
            documents=all_chunks,
            file_count=len(files),
            chunk_count=len(all_chunks),
            indexed_extensions=sorted(indexed_extensions),
            root_path=str(root_path),
        )

    def _collect_files(self, source_path: Path) -> list[Path]:
        if source_path.is_file():
            return [source_path] if self._should_include_file(source_path) else []

        files: list[Path] = []
        for root, dirnames, filenames in os.walk(source_path):
            dirnames[:] = [
                dirname
                for dirname in dirnames
                if dirname not in EXCLUDED_DIRECTORIES and not dirname.startswith(".pytest_cache")
            ]

            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename
                if self._should_include_file(file_path):
                    files.append(file_path)

        return sorted(files)

    def _should_include_file(self, path: Path) -> bool:
        name = path.name
        suffix = path.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            return False
        if name in EXCLUDED_FILENAMES:
            return False
        if any(name.endswith(excluded_suffix) for excluded_suffix in EXCLUDED_SUFFIXES):
            return False
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
        return True

    def _chunk_file(self, file_path: Path, root_path: Path, workspace: str) -> list[Document]:
        documents = TextLoader(str(file_path), autodetect_encoding=True).load()
        splitter = self._get_splitter(file_path.suffix.lower())
        chunks = splitter.split_documents(documents)
        relative_path = str(file_path.relative_to(root_path))
        language = self._get_language_name(file_path.suffix.lower())

        for index, chunk in enumerate(chunks):
            chunk.metadata = {
                **chunk.metadata,
                "workspace": workspace,
                "source": str(file_path),
                "relative_path": relative_path,
                "extension": file_path.suffix.lower(),
                "language": language,
                "chunk_index": index,
            }

        return chunks

    def _get_splitter(self, extension: str) -> RecursiveCharacterTextSplitter:
        language = CODE_LANGUAGE_BY_EXTENSION.get(extension)
        if language is None:
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        return RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def _get_language_name(self, extension: str) -> str:
        language = CODE_LANGUAGE_BY_EXTENSION.get(extension)
        if language is not None:
            return language.name.lower()
        return {
            ".vue": "vue",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".css": "css",
            ".scss": "scss",
            ".txt": "text",
        }.get(extension, "text")

    @staticmethod
    def chunk_preview(document: Document, max_chars: int = 220) -> dict[str, Any]:
        content = " ".join(document.page_content.split())
        return {
            "source": document.metadata.get("source", "unknown"),
            "relative_path": document.metadata.get("relative_path", "unknown"),
            "workspace": document.metadata.get("workspace", "default"),
            "extension": document.metadata.get("extension", ""),
            "language": document.metadata.get("language", "text"),
            "content_preview": content[:max_chars],
            "content": document.page_content,
        }
