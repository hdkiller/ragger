import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";

const DEFAULT_BASE_URL = process.env.RAGGER_BASE_URL ?? "http://127.0.0.1:8170";
const DEFAULT_WORKSPACE = process.env.RAGGER_WORKSPACE ?? "default";
const DEFAULT_TOP_K = Number(process.env.RAGGER_TOP_K ?? "4");

type SearchHit = {
	source: string;
	relative_path: string;
	workspace: string;
	extension: string;
	language?: string;
	score?: number;
	content_preview: string;
	content: string;
};

type SearchResponse = {
	workspace: string;
	query: string;
	results: SearchHit[];
};

type WorkspaceFile = {
	relative_path: string;
	source: string;
	extension: string;
	language?: string;
	chunk_count?: number | null;
};

type WorkspaceFilesResponse = {
	workspace: string;
	files: WorkspaceFile[];
};

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
	const response = await fetch(url, {
		...init,
		headers: {
			accept: "application/json",
			"content-type": "application/json",
			...(init?.headers ?? {}),
		},
	});

	const contentType = response.headers.get("content-type") ?? "";
	if (!response.ok) {
		const text = await response.text();
		throw new Error(`Ragger API ${response.status}: ${text}`);
	}

	if (!contentType.includes("application/json")) {
		const text = await response.text();
		throw new Error(
			`Ragger API returned non-JSON response from ${url}. ` +
				`Check that the server is running on ${baseUrlForMessage(url)}. ` +
				`Response started with: ${text.slice(0, 120)}`,
		);
	}

	return (await response.json()) as T;
}

function baseUrlForMessage(url: string): string {
	try {
		const parsed = new URL(url);
		return parsed.origin;
	} catch {
		return url;
	}
}

function formatHits(hits: SearchHit[]): string {
	if (hits.length === 0) return "No results.";
	return hits
		.map(
			(hit, index) =>
				`${index + 1}. ${hit.relative_path} (${hit.extension})\n${hit.content_preview}`,
		)
		.join("\n\n");
}

export default function raggerExtension(pi: ExtensionAPI) {
	let activeWorkspace = DEFAULT_WORKSPACE;
	let ragEnabled = true;
	const baseUrl = DEFAULT_BASE_URL;

	pi.registerCommand("ragger-workspace", {
		description: "Switch the active ragger workspace",
		handler: async (args, ctx) => {
			const workspace = args.trim();
			if (!workspace) {
				ctx.ui.notify("Usage: /ragger-workspace <name>", "error");
				return;
			}
			activeWorkspace = workspace;
			ctx.ui.notify(`Ragger workspace set to ${workspace}`, "info");
		},
	});

	pi.registerCommand("ragger-on", {
		description: "Enable ragger auto-injection",
		handler: async (_args, ctx) => {
			ragEnabled = true;
			ctx.ui.notify("Ragger auto-injection enabled", "info");
		},
	});

	pi.registerCommand("ragger-off", {
		description: "Disable ragger auto-injection",
		handler: async (_args, ctx) => {
			ragEnabled = false;
			ctx.ui.notify("Ragger auto-injection disabled", "info");
		},
	});

	pi.registerCommand("ragger", {
		description: "Ragger — Local RAG workspace management",
		handler: async (_args, ctx) => {
			ctx.ui.notify("Use the dashboard UI to manage ragger workspaces.", "info");
		},
	});

	pi.registerTool({
		name: "ragger_index",
		label: "Ragger Index",
		description: "Index a file or directory into a named ragger workspace",
		parameters: Type.Object({
			workspace: Type.Optional(Type.String({ description: "Workspace name", default: DEFAULT_WORKSPACE })),
			path: Type.String({ description: "File or directory path to index" }),
			replace: Type.Optional(Type.Boolean({ default: true })),
		}),
		execute: async (_toolCallId, params) => {
			const result = await fetchJson(`${baseUrl}/workspaces/index`, {
				method: "POST",
				body: JSON.stringify({
					workspace: params.workspace ?? activeWorkspace,
					path: params.path,
					replace: params.replace ?? true,
				}),
			});
			if (params.workspace) {
				activeWorkspace = params.workspace;
			}
			return {
				content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
				details: result,
			};
		},
	});

	pi.registerTool({
		name: "ragger_search",
		label: "Ragger Search",
		description: "Search a named ragger workspace through the local FastAPI server",
		parameters: Type.Object({
			workspace: Type.Optional(Type.String({ description: "Workspace name", default: DEFAULT_WORKSPACE })),
			query: Type.String({ description: "Search query" }),
			k: Type.Optional(Type.Number({ default: DEFAULT_TOP_K })),
		}),
		execute: async (_toolCallId, params) => {
			const result = await fetchJson<SearchResponse>(`${baseUrl}/workspaces/search`, {
				method: "POST",
				body: JSON.stringify({
					workspace: params.workspace ?? activeWorkspace,
					query: params.query,
					k: params.k ?? DEFAULT_TOP_K,
				}),
			});
			if (params.workspace) {
				activeWorkspace = params.workspace;
			}
			return {
				content: [{ type: "text", text: formatHits(result.results) }],
				details: result,
			};
		},
	});

	pi.registerTool({
		name: "ragger_status",
		label: "Ragger Status",
		description: "Show ragger server health and workspace stats",
		parameters: Type.Object({
			workspace: Type.Optional(Type.String({ description: "Workspace name", default: DEFAULT_WORKSPACE })),
		}),
		execute: async (_toolCallId, params) => {
			const workspace = params.workspace ?? activeWorkspace;
			const health = await fetchJson(`${baseUrl}/health`);
			let stats: unknown = null;
			try {
				stats = await fetchJson(`${baseUrl}/workspaces/${workspace}/stats`);
			} catch {
				stats = { workspace, status: "not_indexed" };
			}
			return {
				content: [{ type: "text", text: JSON.stringify({ health, stats }, null, 2) }],
				details: { health, stats },
			};
		},
	});

	pi.on("before_agent_start", async (event) => {
		if (!ragEnabled || !event.prompt.trim()) return undefined;

		let result: SearchResponse | null = null;
		try {
			result = await fetchJson<SearchResponse>(`${baseUrl}/workspaces/search`, {
				method: "POST",
				body: JSON.stringify({
					workspace: activeWorkspace,
					query: event.prompt,
					k: DEFAULT_TOP_K,
				}),
			});
		} catch {
			return undefined;
		}

		if (!result.results.length) return undefined;

		const context = result.results
			.map(
				(hit, index) =>
					`[${index + 1}] ${hit.relative_path}\n${hit.content_preview}\n`,
			)
			.join("\n");

		return {
			systemPrompt:
				`${event.systemPrompt}\n\n` +
				`## Ragger Context\n` +
				`The following snippets were retrieved from the local workspace \`${activeWorkspace}\`.\n` +
				`Use them when relevant, cite file paths when helpful, and do not pretend you saw files that are not listed.\n\n` +
				context,
		};
	});

	// ── Dashboard Extension UI ──────────────────────────────────────

	const raggerBaseUrl = baseUrl; // capture for closures

	// ── Dashboard data cache ─────────────────────────────────────
	// The bridge's ui:get-data flow is synchronous — it checks probe.items
	// immediately after emit(). Async handlers (HTTP fetch) won't work.
	// Solution: background polling refreshes a cache, ui:get-data reads synchronously.

	const raggerCache: {
		health: { connected: boolean; workspaceCount: number; embeddingModel: string; activeWorkspace: string };
		workspaces: any[];
		files: any[];
		searchResults: any[];
	} = {
		health: { connected: false, workspaceCount: 0, embeddingModel: "", activeWorkspace: DEFAULT_WORKSPACE },
		workspaces: [],
		files: [],
		searchResults: [],
	};

	let raggerCacheTimer: ReturnType<typeof setInterval> | null = null;
	let filesWorkspace = DEFAULT_WORKSPACE;

	const syncDerivedWorkspaceState = () => {
		raggerCache.health.activeWorkspace = activeWorkspace;
		raggerCache.workspaces = raggerCache.workspaces.map((workspace: any) => ({
			...workspace,
			is_active: workspace.workspace === activeWorkspace,
			active_badge: workspace.workspace === activeWorkspace ? "Active" : [],
		}));
	};

	const loadWorkspaceFiles = async (workspace: string): Promise<WorkspaceFile[]> => {
		const result = await fetchJson<WorkspaceFilesResponse>(`${raggerBaseUrl}/workspaces/${workspace}/files`);
		return result.files ?? [];
	};

	const refreshRaggerCache = async () => {
		try {
			const health: any = await fetchJson(`${raggerBaseUrl}/health`);
			raggerCache.health = {
				connected: true,
				workspaceCount: health.workspace_count ?? 0,
				embeddingModel: health.embedding_model ?? "unknown",
				activeWorkspace,
			};
		} catch {
			raggerCache.health = { connected: false, workspaceCount: 0, embeddingModel: "unreachable", activeWorkspace };
		}
		try {
			const result: any = await fetchJson(`${raggerBaseUrl}/workspaces`);
			raggerCache.workspaces = (result.workspaces ?? []).map((ws: any) => ({
				...ws,
				indexed_extensions: ws.indexed_extensions ?? [],
			}));
			syncDerivedWorkspaceState();
		} catch {
			raggerCache.workspaces = [];
		}
		// Also refresh the file list for the active workspace
		try {
			filesWorkspace = activeWorkspace;
			raggerCache.files = await loadWorkspaceFiles(activeWorkspace);
		} catch {
			raggerCache.files = [];
		}
	};

	raggerCacheTimer = setInterval(refreshRaggerCache, 30_000);
	refreshRaggerCache().then(() => {
		pi.events.emit("ragger:change", { type: "cache-ready" });
	}).catch(() => {});

	// Register UI module for the dashboard
	pi.events.on("ui:list-modules", (data: any) => {
		data.modules.push({
			id: "ragger",
			title: "Ragger — Local RAG",
			icon: "databaseSearch",
			command: "/ragger",
			initialViewId: "status",
			presentation: {
				dialogSize: "wide",
			},
			statusBarControls: [
				{
					id: "active-workspace",
					type: "chip",
					label: "RAG",
					icon: "databaseSearch",
					title: "Open Ragger workspace manager",
					dataEvent: "ragger:status",
					valueKey: "activeWorkspace",
					active: true,
					action: {
						label: "Open Ragger",
						emit: "ui:open-module",
						params: { viewId: "workspaces" },
					},
				},
			],
			views: [
				{
					id: "status",
					type: "metrics",
					title: "Overview",
					dataEvent: "ragger:status",
					metricsConfig: {
						cards: [
							{ key: "activeWorkspace", label: "Active Workspace", icon: "folder", format: "text", color: "#f59e0b", size: "prominent", helperText: "This workspace is used for inline RAG context and modal search by default." },
							{ key: "connected", label: "Connection", icon: "lanConnect", format: "boolean", color: "#34d399", helperText: "Local server availability" },
							{ key: "workspaceCount", label: "Indexed Workspaces", icon: "folderMultiple", format: "number", color: "#60a5fa", helperText: "Available local knowledge sets" },
							{ key: "embeddingModel", label: "Embeddings", icon: "brain", format: "text", color: "#93c5fd", helperText: "Embedding model currently backing search" },
						],
					},
					actions: [
						{ label: "Workspaces", icon: "folderMultiple", emit: "ui:navigate", params: { viewId: "workspaces" } },
						{ label: "Search", icon: "magnify", emit: "ui:navigate", params: { viewId: "search" } },
					],
				},
				{
					id: "workspaces",
					type: "table",
					title: "Workspaces",
					dataEvent: "ragger:list-workspaces",
					updateEvent: "ragger:change",
					tableConfig: {
						activeKey: "is_active",
					},
					fields: [
						{ key: "active_badge", label: "State", type: "badge", color: "bg-emerald-500/15 text-emerald-400" },
						{ key: "workspace", label: "Name", type: "text" },
						{ key: "file_count", label: "Files", type: "number" },
						{ key: "chunk_count", label: "Chunks", type: "number" },
						{ key: "indexed_extensions", label: "Extensions", type: "badge" },
						{ key: "last_indexed_at", label: "Last Indexed", type: "datetime" },
					],
					itemActions: [
						{ label: "Set Active", icon: "folder", emit: "ragger:set-active", primaryParam: "workspace" },
						{ label: "Files", icon: "fileMultiple", emit: "ragger:view-files", primaryParam: "workspace", navigateTo: "files" },
						{ label: "Re-index", icon: "refresh", emit: "ragger:reindex-request", primaryParam: "workspace" },
						{ label: "Delete", icon: "trashCanOutline", emit: "ragger:delete-request", primaryParam: "workspace", variant: "danger", confirm: "Delete this workspace and all its indexed data?" },
					],
					actions: [
						{ label: "Index New", icon: "plus", emit: "ui:navigate", params: { viewId: "index" }, variant: "primary" },
						{ label: "Search Active", icon: "magnify", emit: "ui:navigate", params: { viewId: "search" } },
					],
				},
				{
					id: "index",
					type: "form",
					title: "Index Workspace",
					fields: [
						{ key: "workspace", label: "Workspace Name", type: "text", required: true, placeholder: "default" },
						{ key: "path", label: "Path to Index", type: "text", required: true, placeholder: "/path/to/codebase" },
						{
							key: "replace", label: "Mode", type: "select", options: [
								{ label: "Full reindex (replace)", value: true },
								{ label: "Incremental (keep existing)", value: false },
							],
						},
					],
					actions: [
						{ label: "Cancel", emit: "ui:navigate", params: { viewId: "workspaces" } },
						{ label: "Start Indexing", icon: "database", emit: "ragger:index-request", variant: "primary" },
					],
				},
				{
					id: "search",
					type: "search",
					title: "Search",
					searchConfig: {
						placeholder: "Search indexed code...",
						resultDataEvent: "ragger:search",
						resultFields: [
							{ key: "relative_path", label: "File", type: "link" },
							{ key: "score", label: "Score", type: "number" },
							{ key: "language", label: "Lang", type: "badge" },
							{ key: "content_preview", label: "Preview", type: "snippet" },
						],
						resultActions: [
							{ label: "Copy Path", icon: "contentCopy", emit: "ragger:copy-path", primaryParam: "relative_path" },
						],
						debounceMs: 300,
						minQueryLength: 2,
					},
				},
				{
					id: "files",
					type: "table",
					title: "Indexed Files",
					dataEvent: "ragger:list-files",
					updateEvent: "ragger:files-updated",
					fields: [
						{ key: "relative_path", label: "Path", type: "link" },
						{ key: "extension", label: "Type", type: "badge" },
						{ key: "language", label: "Language", type: "text" },
						{ key: "chunk_count", label: "Chunks", type: "number" },
					],
					actions: [
						{ label: "Back", icon: "arrowLeft", emit: "ui:navigate", params: { viewId: "workspaces" } },
					],
				},
			],
		});
	});

	// Provide data for dashboard views — SYNCHRONOUS reads from cache
	pi.events.on("ui:get-data", (data: any) => {
		if (data.event === "ragger:status") {
			// Update active workspace in cached health before returning
			raggerCache.health.activeWorkspace = activeWorkspace;
			data.items = [raggerCache.health];
		} else if (data.event === "ragger:list-workspaces") {
			data.items = raggerCache.workspaces;
		} else if (data.event === "ragger:search") {
			const query = typeof data.query === "string" ? data.query.trim() : "";
			const workspace = typeof data.workspace === "string" && data.workspace.trim()
				? data.workspace.trim()
				: activeWorkspace;
			if (!query) {
				raggerCache.searchResults = [];
				data.items = [];
				return;
			}
			data.itemsPromise = triggerRaggerSearch(query, workspace).then(() => raggerCache.searchResults);
		} else if (data.event === "ragger:list-files") {
			const workspace = typeof data.workspace === "string" && data.workspace.trim()
				? data.workspace.trim()
				: filesWorkspace;
			data.itemsPromise = loadWorkspaceFiles(workspace).then((files) => {
				filesWorkspace = workspace;
				raggerCache.files = files;
				return files;
			});
		}
	});

	// Async helpers that update cache and emit change events
	const triggerRaggerSearch = async (query: string, workspace?: string) => {
		if (!query) { raggerCache.searchResults = []; return; }
		try {
			const result = await fetchJson<SearchResponse>(`${raggerBaseUrl}/workspaces/search`, {
				method: "POST",
				body: JSON.stringify({ workspace: workspace ?? activeWorkspace, query, k: 8 }),
			});
			raggerCache.searchResults = result.results;
		} catch {
			raggerCache.searchResults = [];
		}
	};

	// Handle dashboard actions
	pi.events.on("ragger:set-active", async (params: any) => {
		const workspace = params.workspace;
		if (!workspace) return;
		activeWorkspace = workspace;
		syncDerivedWorkspaceState();
		// Refresh file list for the newly active workspace
		try {
			filesWorkspace = workspace;
			raggerCache.files = await loadWorkspaceFiles(workspace);
		} catch {
			raggerCache.files = [];
		}
		pi.events.emit("ragger:change", { type: "workspace-changed", workspace });
		pi.events.emit("flow:notify", { message: `Active workspace set to "${workspace}"`, level: "info" });
	});

	pi.events.on("ragger:view-files", async (params: any) => {
		const workspace = params.workspace;
		if (!workspace) return;
		// Load files for this specific workspace (not necessarily the active one)
		try {
			filesWorkspace = workspace;
			raggerCache.files = await loadWorkspaceFiles(workspace);
		} catch {
			raggerCache.files = [];
		}
		// Emit update so the files view refreshes
		pi.events.emit("ragger:files-updated", { type: "files-loaded", workspace });
	});

	pi.events.on("ragger:index-request", async (params: any) => {
		try {
			await fetchJson(`${raggerBaseUrl}/workspaces/index`, {
				method: "POST",
				body: JSON.stringify({
					workspace: params.workspace || activeWorkspace,
					path: params.path,
					replace: params.replace !== "false",
				}),
			});
			await refreshRaggerCache();
			pi.events.emit("ragger:change", { type: "indexed", workspace: params.workspace });
			pi.events.emit("flow:notify", { message: `Workspace "${params.workspace}" indexed successfully.`, level: "success" });
		} catch (err: any) {
			pi.events.emit("flow:notify", { message: `Indexing failed: ${err.message}`, level: "error" });
		}
	});

	pi.events.on("ragger:reindex-request", async (params: any) => {
		const workspace = params.workspace;
		if (!workspace) return;
		try {
			const stats: any = await fetchJson(`${raggerBaseUrl}/workspaces/${workspace}/stats`);
			await fetchJson(`${raggerBaseUrl}/workspaces/index`, {
				method: "POST",
				body: JSON.stringify({ workspace, path: stats.root_path, replace: true }),
			});
			await refreshRaggerCache();
			pi.events.emit("ragger:change", { type: "reindexed", workspace });
			pi.events.emit("flow:notify", { message: `Workspace "${workspace}" re-indexed.`, level: "success" });
		} catch (err: any) {
			pi.events.emit("flow:notify", { message: `Re-index failed: ${err.message}`, level: "error" });
		}
	});

	pi.events.on("ragger:delete-request", async (params: any) => {
		const workspace = params.workspace;
		if (!workspace) return;
		try {
			await fetchJson(`${raggerBaseUrl}/workspaces/${workspace}`, { method: "DELETE" });
			await refreshRaggerCache();
			if (activeWorkspace === workspace) {
				activeWorkspace = DEFAULT_WORKSPACE;
				syncDerivedWorkspaceState();
			}
			pi.events.emit("ragger:change", { type: "deleted", workspace });
			pi.events.emit("flow:notify", { message: `Workspace "${workspace}" deleted.`, level: "info" });
		} catch (err: any) {
			pi.events.emit("flow:notify", { message: `Delete failed: ${err.message}`, level: "error" });
		}
	});

	pi.events.on("ragger:navigate-search", (params: any) => {
		if (params.workspace) activeWorkspace = params.workspace;
	});

	pi.events.on("ragger:copy-path", (params: any) => {
		pi.events.emit("flow:notify", { message: `Copied: ${params.relative_path}`, level: "info" });
	});
}
