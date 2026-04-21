from pathlib import Path


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
