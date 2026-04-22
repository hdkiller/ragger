from pathlib import Path


def render_help_text(current_workspace: str) -> str:
    return "\n".join(
        [
            "## Help",
            "",
            "Commands:",
            "- `/ingest <path>` indexes a path into the current workspace.",
            "- `/ingest <workspace> <path>` indexes a path into a named workspace.",
            "- `/workspace <name>` switches the active workspace.",
            "- `/list` shows indexed files for the active workspace.",
            "- `/list <workspace>` shows indexed files for a named workspace.",
            "- `/workspaces` shows all indexed workspaces and summary stats.",
            "- `/stats` shows stats for the active workspace.",
            "- `/stats <workspace>` shows stats for a named workspace.",
            "- `/clear` removes the active workspace from Chroma and metadata.",
            "- `/clear <workspace>` removes a named workspace from Chroma and metadata.",
            "- `/help` shows this command guide.",
            "",
            f"Active workspace: `{current_workspace}`",
            "",
            "Tips:",
            "- Ask a normal question to search the active workspace and stream an answer.",
            "- The sidebar shows indexed workspaces and the files currently stored for the active workspace.",
            "- Use `/workspaces` before `/clear` if you want a quick safety check.",
        ]
    )


def parse_list_args(raw_args: str, current_workspace: str) -> str:
    workspace = raw_args.strip()
    return workspace or current_workspace


def parse_workspace_arg(raw_args: str, current_workspace: str) -> str:
    workspace = raw_args.strip()
    return workspace or current_workspace


def render_workspace_file_list(workspace: str, files: list[dict], max_files: int = 50) -> str:
    if not files:
        return "\n".join(
            [
                f"## Indexed Files: `{workspace}`",
                "",
                "No indexed files found for this workspace.",
            ]
        )

    lines = [
        f"## Indexed Files: `{workspace}`",
        "",
        f"Showing {min(len(files), max_files)} of {len(files)} files.",
        "",
    ]
    for file_info in files[:max_files]:
        chunk_count = file_info.get("chunk_count")
        chunk_text = f"{chunk_count} chunks" if chunk_count is not None else "chunk count unavailable"
        lines.append(
            f"- `{file_info['relative_path']}` [{file_info.get('language', 'text')}, {chunk_text}]"
        )

    hidden_count = len(files) - min(len(files), max_files)
    if hidden_count > 0:
        lines.extend(["", f"... and {hidden_count} more files."])

    return "\n".join(lines)


def render_workspace_stats_text(workspace: str, stats: dict) -> str:
    return "\n".join(
        [
            f"## Workspace Stats: `{workspace}`",
            "",
            f"- Root: `{stats['root_path']}`",
            f"- Files: **{stats['file_count']}**",
            f"- Chunks: **{stats['chunk_count']}**",
            f"- Extensions: `{', '.join(stats['indexed_extensions']) or 'none'}`",
            f"- Collection: `{stats['collection_name']}`",
            f"- Indexed: `{stats['last_indexed_at']}`",
            f"- LLM: `{stats['model']}`",
            f"- Embeddings: `{stats['embedding_model']}`",
        ]
    )


def render_workspaces_overview(workspaces: list[dict]) -> str:
    if not workspaces:
        return "\n".join(
            [
                "## Workspaces",
                "",
                "No indexed workspaces yet.",
            ]
        )

    lines = [
        "## Workspaces",
        "",
        f"Indexed workspaces: **{len(workspaces)}**",
        "",
    ]
    for workspace in workspaces:
        lines.extend(
            [
                f"### `{workspace['workspace']}`",
                f"- Root: `{workspace['root_path']}`",
                f"- Files: {workspace['file_count']}",
                f"- Chunks: {workspace['chunk_count']}",
                f"- Indexed: `{workspace['last_indexed_at']}`",
            ]
        )
    return "\n".join(lines)


def render_clear_result(workspace: str, deleted: bool) -> str:
    if deleted:
        message = "Workspace removed from Chroma and local metadata."
    else:
        message = "Workspace was not present in local metadata, but any matching collection cleanup was attempted."
    return "\n".join(
        [
            f"## Clear Workspace: `{workspace}`",
            "",
            message,
        ]
    )


def parse_ingest_args(raw_args: str, current_workspace: str) -> tuple[str, Path]:
    raw_args = raw_args.strip()
    if not raw_args:
        raise ValueError("Usage: /ingest <path> or /ingest <workspace> <path>")

    whole_path = Path(raw_args).expanduser()
    if not whole_path.is_absolute():
        whole_path = Path.cwd() / whole_path
    if whole_path.exists():
        return current_workspace, whole_path.resolve()

    parts = raw_args.split()
    if len(parts) == 1:
        workspace = current_workspace
        path_text = parts[0]
    else:
        workspace = parts[0]
        path_text = " ".join(parts[1:])

    resolved_path = Path(path_text).expanduser()
    if not resolved_path.is_absolute():
        resolved_path = Path.cwd() / resolved_path
    return workspace, resolved_path.resolve()
