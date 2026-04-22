import argparse
import json

from ragger.config import DEFAULT_WORKSPACE
from ragger.core.workspaces import RAGWorkspaceManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Ragger CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index a file or directory into a workspace")
    index_parser.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)
    index_parser.add_argument("path")
    index_parser.add_argument(
        "--append", action="store_true", help="Append without replacing the workspace"
    )

    stats_parser = subparsers.add_parser("stats", help="Show workspace stats")
    stats_parser.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)

    workspaces_parser = subparsers.add_parser("workspaces", help="List indexed workspaces")

    search_parser = subparsers.add_parser("search", help="Search a workspace")
    search_parser.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)
    search_parser.add_argument("query")
    search_parser.add_argument("-k", type=int, default=5)

    list_parser = subparsers.add_parser("list", help="List indexed files in a workspace")
    list_parser.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)

    clear_parser = subparsers.add_parser("clear", help="Delete a workspace collection and metadata")
    clear_parser.add_argument("workspace", nargs="?", default=DEFAULT_WORKSPACE)

    args = parser.parse_args()
    manager = RAGWorkspaceManager()

    if args.command == "index":
        result = manager.ingest_workspace(
            workspace=args.workspace,
            path=args.path,
            replace=not args.append,
        )
        print(json.dumps(result, indent=2))
        return

    if args.command == "stats":
        print(json.dumps(manager.get_workspace_stats(args.workspace), indent=2))
        return

    if args.command == "workspaces":
        print(json.dumps(manager.list_workspaces(), indent=2))
        return

    if args.command == "search":
        print(
            json.dumps(
                manager.search_workspace(workspace=args.workspace, query=args.query, k=args.k),
                indent=2,
            )
        )
        return

    if args.command == "list":
        print(json.dumps(manager.list_workspace_files(args.workspace), indent=2))
        return

    if args.command == "clear":
        print(json.dumps(manager.delete_workspace(args.workspace), indent=2))


if __name__ == "__main__":
    main()
