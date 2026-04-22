from __future__ import annotations


def render_ingest_progress(
    workspace: str,
    current_file: int | None,
    total_files: int | None,
    current_path: str | None,
    active: bool,
) -> str:
    if not active or not total_files:
        return "## Indexing\n\nIdle."

    completed = min(current_file or 0, total_files)
    width = 16
    filled = max(0, min(width, round((completed / total_files) * width)))
    bar = f"[{'#' * filled}{'.' * (width - filled)}]"
    lines = [
        "## Indexing",
        "",
        f"- Workspace: `{workspace}`",
        f"- Progress: {bar} {completed}/{total_files}",
    ]
    if current_path:
        lines.append(f"- File: `{current_path}`")
    return "\n".join(lines)


def render_stats_panel(
    current_workspace: str,
    health: dict,
    stats: dict | None,
    last_ingest_summary: str,
) -> str:
    if stats is None:
        workspace_section = [
            "## Workspace",
            f"- Active: `{current_workspace}`",
            "- Status: not indexed yet",
            f"- Ollama: `{'up' if health['ollama']['reachable'] else 'down'}`",
            "- Server mode: local core",
            "",
            last_ingest_summary,
        ]
    else:
        workspace_section = [
            "## Workspace",
            f"- Active: `{current_workspace}`",
            f"- Root: `{stats['root_path']}`",
            f"- Files: **{stats['file_count']}**",
            f"- Chunks: **{stats['chunk_count']}**",
            f"- Extensions: `{', '.join(stats['indexed_extensions']) or 'none'}`",
            f"- Collection: `{stats['collection_name']}`",
            f"- Indexed: `{stats['last_indexed_at']}`",
            f"- Ollama: `{'up' if health['ollama']['reachable'] else 'down'}`",
            f"- LLM: `{stats['model']}`",
            f"- Embeddings: `{stats['embedding_model']}`",
            "",
            last_ingest_summary,
        ]
    return "\n".join(workspace_section)


def render_workspace_browser(
    workspaces: list[dict],
    current_workspace: str,
    files: list[dict],
    max_files: int = 12,
) -> str:
    lines = ["## Indexed Browser", "", "### Workspaces"]

    if not workspaces:
        lines.extend(
            [
                "- No indexed workspaces yet.",
                "",
                "Use `/ingest <path>` to add one.",
            ]
        )
        return "\n".join(lines)

    for workspace in workspaces:
        name = workspace.get("workspace", "unknown")
        marker = " (active)" if name == current_workspace else ""
        file_count = workspace.get("file_count", 0)
        chunk_count = workspace.get("chunk_count", 0)
        lines.append(f"- `{name}`{marker}: {file_count} files / {chunk_count} chunks")

    lines.extend(["", f"### Files In `{current_workspace}`"])
    if not files:
        lines.append("- No indexed files in the active workspace.")
        return "\n".join(lines)

    visible_files = files[:max_files]
    for file_info in visible_files:
        chunk_count = file_info.get("chunk_count")
        chunk_text = f"{chunk_count} chunks" if chunk_count is not None else "chunks unknown"
        lines.append(
            f"- `{file_info['relative_path']}` [{file_info['language']}, {chunk_text}]"
        )

    hidden_count = len(files) - len(visible_files)
    if hidden_count > 0:
        lines.extend(
            [
                "",
                f"... and {hidden_count} more files.",
            ]
        )

    return "\n".join(lines)


def render_retrieval_panel(docs, current_workspace: str) -> str:
    if not docs:
        return "## Retrieval\n\nNo matches found for the active workspace."

    lines = [f"## Retrieval\n\nUsing workspace `{current_workspace}`"]
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("relative_path", doc.metadata.get("source", "unknown"))
        preview = " ".join(doc.page_content.strip().split())[:180]
        lines.extend(
            [
                f"### Hit {index}",
                f"- Source: `{source}`",
                f"- Language: `{doc.metadata.get('language', 'text')}`",
                f"- Preview: {preview}...",
            ]
        )
    return "\n".join(lines)
