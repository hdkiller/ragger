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
