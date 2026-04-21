import os

from ragger.core.workspaces import RAGWorkspaceManager


if __name__ == "__main__":
    path = os.getcwd()
    print(f"Ingesting workspace 'default' from: {path}")
    manager = RAGWorkspaceManager()
    stats = manager.ingest_workspace("default", path, replace=True)
    print(
        f"Done! Indexed {stats['file_count']} files into {stats['chunk_count']} chunks "
        f"for extensions: {', '.join(stats['indexed_extensions'])}"
    )
