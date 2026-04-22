import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Log, Markdown, Static

from ragger.config import DEFAULT_WORKSPACE
from ragger.core.search import RAGEngine
from ragger.core.workspaces import RAGWorkspaceManager
from ragger.tui.commands import (
    parse_ingest_args,
    parse_list_args,
    parse_workspace_arg,
    render_clear_result,
    render_help_text,
    render_workspace_stats_text,
    render_workspace_file_list,
    render_workspaces_overview,
)
from ragger.tui.panels import (
    render_ingest_progress,
    render_retrieval_panel,
    render_stats_panel,
    render_workspace_browser,
)


class RaggerApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    #main-container {
        height: 1fr;
        padding: 1;
    }
    #chat-area {
        height: 1fr;
        border: solid $primary;
        overflow-y: auto;
        padding: 1;
        margin-bottom: 1;
    }
    Input {
        dock: bottom;
        margin-top: 1;
    }
    #status-sidebar {
        width: 52;
        dock: right;
        border-left: solid $accent;
        padding: 1;
        background: $surface-darken-1;
    }
    .panel-title {
        margin-bottom: 1;
    }
    #stats-panel {
        height: 13;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }
    #progress-panel {
        height: 7;
        border: solid $primary-lighten-1;
        padding: 1;
        margin-bottom: 1;
    }
    #browser-panel {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
    }
    #retrieval-panel {
        height: 12;
        border: solid $warning;
        padding: 1;
        margin-bottom: 1;
    }
    #status-log {
        height: 10;
        border: solid $success;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=True),
    ]

    def on_mount(self):
        self.manager = RAGWorkspaceManager()
        self.current_workspace = DEFAULT_WORKSPACE
        self.engine = RAGEngine(manager=self.manager, workspace=self.current_workspace)
        self.chat_history = (
            "## Ragger\n\n"
            "Use `/ingest <path>` or `/ingest <workspace> <path>` to index a repo.\n\n"
            "Use `/workspace <name>` to switch the active workspace.\n\n"
            "Use `/list` to browse indexed files.\n\n"
            "Use `/help` to see all commands."
        )
        self.last_ingest_summary = "No ingestion yet."
        self.ingest_active = False
        self.ingest_workspace_name = self.current_workspace
        self.ingest_current_file = None
        self.ingest_total_files = None
        self.ingest_current_path = None
        self.log_widget = self.query_one("#status-log", Log)
        self.chat_area = self.query_one("#chat-area", Markdown)
        self.stats_area = self.query_one("#stats-panel", Markdown)
        self.progress_area = self.query_one("#progress-panel", Markdown)
        self.browser_area = self.query_one("#browser-panel", Markdown)
        self.retrieval_area = self.query_one("#retrieval-panel", Markdown)
        self.chat_area.update(self.chat_history)
        self.retrieval_area.update("## Retrieval\n\nNo query yet.")
        self.update_status_panels()
        self.log_widget.write_line("System ready.")
        self.log_widget.write_line("Try: /ingest default tmp/alice.txt")
        self.log_widget.write_line("Use /help for command reference.")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="main-container"):
                yield Markdown(id="chat-area")
                yield Input(placeholder="Ask a question or run /ingest ...", id="query-input")
            with Vertical(id="status-sidebar"):
                yield Static("Workspace + Chroma", classes="panel-title")
                yield Markdown(id="stats-panel")
                yield Static("Index Progress", classes="panel-title")
                yield Markdown(id="progress-panel")
                yield Static("Indexed Files", classes="panel-title")
                yield Markdown(id="browser-panel")
                yield Static("RAG Retrieval", classes="panel-title")
                yield Markdown(id="retrieval-panel")
                yield Static("Engine Log", classes="panel-title")
                yield Log(id="status-log")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted):
        query = event.value.strip()
        if not query:
            return

        input_widget = self.query_one("#query-input", Input)
        input_widget.value = ""

        if query.startswith("/ingest "):
            await self.run_ingestion(query.removeprefix("/ingest ").strip())
        elif query.startswith("/workspace "):
            self.switch_workspace(query.removeprefix("/workspace ").strip())
        elif query == "/list" or query.startswith("/list "):
            self.show_file_list(query.removeprefix("/list").strip())
        elif query == "/workspaces":
            self.show_workspaces()
        elif query == "/stats" or query.startswith("/stats "):
            self.show_workspace_stats(query.removeprefix("/stats").strip())
        elif query == "/clear" or query.startswith("/clear "):
            self.clear_workspace(query.removeprefix("/clear").strip())
        elif query == "/help":
            self.show_help()
        else:
            await self.run_query(query)

    async def run_ingestion(self, raw_args: str):
        workspace, resolved_path = parse_ingest_args(raw_args, self.current_workspace)
        self.log_widget.write_line(f"Ingesting into `{workspace}`: {resolved_path}")
        self.ingest_active = True
        self.ingest_workspace_name = workspace
        self.ingest_current_file = 0
        self.ingest_total_files = None
        self.ingest_current_path = None
        self.update_status_panels()

        def report_progress(progress):
            self.call_from_thread(self._apply_ingest_progress, progress)

        try:
            loop = asyncio.get_running_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self.manager.ingest_workspace(
                    workspace=workspace,
                    path=str(resolved_path),
                    replace=True,
                    progress_callback=report_progress,
                ),
            )
            self.current_workspace = workspace
            self.engine.set_workspace(workspace)
            self.last_ingest_summary = f"Last ingest: `{workspace}` with {stats['file_count']} files / {stats['chunk_count']} chunks"
            self.log_widget.write_line(
                f"Indexed {stats['file_count']} files and {stats['chunk_count']} chunks into `{workspace}`."
            )
            self.update_status_panels()
        except Exception as exc:
            self.log_widget.write_line(f"Ingest error: {exc}")
        finally:
            self.ingest_active = False
            self.ingest_current_file = None
            self.ingest_total_files = None
            self.ingest_current_path = None
            self.update_status_panels()

    async def run_query(self, query: str):
        self.chat_history += f"\n\n**You:** {query}\n\n**Gemma:** "
        self.chat_area.update(self.chat_history)
        self.retrieval_area.update("## Retrieval\n\nSearching Chroma...")
        self.log_widget.write_line(f"Retrieving from `{self.current_workspace}` for: {query}")

        full_response = ""
        try:
            loop = asyncio.get_running_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.engine.retrieve(query, workspace=self.current_workspace),
            )
            self.retrieval_area.update(render_retrieval_panel(docs, self.current_workspace))
            if not docs:
                self.log_widget.write_line("No retrieval hits found.")
            else:
                self.log_widget.write_line(f"Retrieved {len(docs)} chunks from Chroma.")
            for chunk in self.engine.stream_answer(query, docs):
                full_response += chunk
                self.chat_area.update(self.chat_history + full_response)
                await asyncio.sleep(0)
            self.chat_history += full_response
            self.log_widget.write_line("Response complete.")
            self.update_status_panels()
        except Exception as exc:
            self.log_widget.write_line(f"Query error: {exc}")

    def switch_workspace(self, workspace: str):
        if not workspace:
            self.log_widget.write_line("Workspace name cannot be empty.")
            return
        self.current_workspace = workspace
        self.engine.set_workspace(workspace)
        self.log_widget.write_line(f"Switched workspace to `{workspace}`.")
        self.update_status_panels()

    def action_clear_chat(self):
        self.chat_history = (
            "## Ragger\n\n"
            "Use `/ingest <path>` or `/ingest <workspace> <path>` to index a repo.\n\n"
            "Use `/workspace <name>` to switch the active workspace.\n\n"
            "Use `/list` to browse indexed files.\n\n"
            "Use `/help` to see all commands."
        )
        self.chat_area.update(self.chat_history)

    def show_help(self):
        self.chat_history += f"\n\n{render_help_text(self.current_workspace)}"
        self.chat_area.update(self.chat_history)
        self.log_widget.write_line("Displayed help.")

    def show_file_list(self, raw_args: str):
        workspace = parse_list_args(raw_args, self.current_workspace)
        try:
            files = self.engine.list_workspace_files(workspace)
            self.chat_history += f"\n\n{render_workspace_file_list(workspace, files)}"
            self.chat_area.update(self.chat_history)
            self.log_widget.write_line(f"Listed {len(files)} files for `{workspace}`.")
        except Exception as exc:
            self.log_widget.write_line(f"List error: {exc}")

    def show_workspaces(self):
        try:
            workspaces = self.engine.list_workspaces()
            self.chat_history += f"\n\n{render_workspaces_overview(workspaces)}"
            self.chat_area.update(self.chat_history)
            self.log_widget.write_line(f"Listed {len(workspaces)} workspaces.")
        except Exception as exc:
            self.log_widget.write_line(f"Workspaces error: {exc}")

    def show_workspace_stats(self, raw_args: str):
        workspace = parse_workspace_arg(raw_args, self.current_workspace)
        try:
            stats = self.engine.get_stats(workspace)
            self.chat_history += f"\n\n{render_workspace_stats_text(workspace, stats)}"
            self.chat_area.update(self.chat_history)
            self.log_widget.write_line(f"Displayed stats for `{workspace}`.")
        except Exception as exc:
            self.log_widget.write_line(f"Stats error: {exc}")

    def clear_workspace(self, raw_args: str):
        workspace = parse_workspace_arg(raw_args, self.current_workspace)
        try:
            result = self.manager.delete_workspace(workspace)
            self.chat_history += f"\n\n{render_clear_result(workspace, result['deleted'])}"
            self.chat_area.update(self.chat_history)
            if workspace == self.current_workspace:
                self.current_workspace = DEFAULT_WORKSPACE
                self.engine.set_workspace(self.current_workspace)
            self.last_ingest_summary = f"Cleared workspace `{workspace}`."
            self.update_status_panels()
            self.log_widget.write_line(f"Cleared workspace `{workspace}`.")
        except Exception as exc:
            self.log_widget.write_line(f"Clear error: {exc}")

    def update_status_panels(self):
        health = self.engine.get_health()
        try:
            stats = self.engine.get_stats(self.current_workspace)
        except Exception:
            stats = None
        try:
            workspace_files = self.engine.list_workspace_files(self.current_workspace)
        except Exception:
            workspace_files = []
        try:
            workspaces = self.engine.list_workspaces()
        except Exception:
            workspaces = []
        self.stats_area.update(
            render_stats_panel(
                current_workspace=self.current_workspace,
                health=health,
                stats=stats,
                last_ingest_summary=self.last_ingest_summary,
            )
        )
        self.progress_area.update(
            render_ingest_progress(
                workspace=self.ingest_workspace_name,
                current_file=self.ingest_current_file,
                total_files=self.ingest_total_files,
                current_path=self.ingest_current_path,
                active=self.ingest_active,
            )
        )
        self.browser_area.update(
            render_workspace_browser(
                workspaces=workspaces,
                current_workspace=self.current_workspace,
                files=workspace_files,
            )
        )

    def _apply_ingest_progress(self, progress) -> None:
        self.ingest_active = True
        self.ingest_workspace_name = progress.workspace
        self.ingest_current_file = progress.current_file
        self.ingest_total_files = progress.total_files
        self.ingest_current_path = progress.relative_path
        self.progress_area.update(
            render_ingest_progress(
                workspace=self.ingest_workspace_name,
                current_file=self.ingest_current_file,
                total_files=self.ingest_total_files,
                current_path=self.ingest_current_path,
                active=True,
            )
        )
        self.log_widget.write_line(
            f"Indexing {progress.current_file}/{progress.total_files}: {progress.relative_path} ({progress.chunk_count} chunks)"
        )


def main() -> None:
    app = RaggerApp()
    app.run()


if __name__ == "__main__":
    main()
