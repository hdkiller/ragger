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
}
