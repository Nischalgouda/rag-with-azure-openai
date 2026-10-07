import { ApiError, toApiError } from "./errors";
import { askResponseSchema } from "./schema";
import type { AskParams, AskResult, Quota } from "./types";

function readQuota(res: Response): Quota | undefined {
  const limit = res.headers.get("X-Daily-Limit");
  const remaining = res.headers.get("X-Daily-Remaining");
  if (limit === null || remaining === null) return undefined;
  const parsed = { limit: Number(limit), remaining: Number(remaining) };
  return Number.isFinite(parsed.limit) && Number.isFinite(parsed.remaining) ? parsed : undefined;
}

/**
 * POST /ask. In development the Vite dev server proxies /api/* to the FastAPI backend; in production
 * the same origin serves both. With `npm run mock` the network is bypassed and deterministic mock
 * data is used instead.
 */
export async function askQuestion(params: AskParams): Promise<AskResult> {
  if (import.meta.env.MODE === "mock") {
    const { mockAsk } = await import("./mock");
    return mockAsk(params);
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (params.apiKey) headers["X-API-Key"] = params.apiKey;

  let res: Response;
  try {
    res = await fetch("/api/ask", {
      method: "POST",
      headers,
      body: JSON.stringify({
        question: params.question,
        mode: params.mode,
        trace: true, // ask the backend for the per-stage retrieval trace (see docs/api-contract.md)
        ...(params.sessionId ? { session_id: params.sessionId } : {}),
      }),
      ...(params.signal ? { signal: params.signal } : {}),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("network", "Could not reach the server. Check your connection and try again.");
  }

  if (!res.ok) throw await toApiError(res);

  let json: unknown;
  try {
    json = await res.json();
  } catch {
    throw new ApiError("contract", "The server returned a response that is not valid JSON.");
  }
  const parsed = askResponseSchema.safeParse(json);
  if (!parsed.success) {
    throw new ApiError("contract", "The server's response did not match the expected format.");
  }
  const quota = readQuota(res);
  return quota ? { ...parsed.data, quota } : parsed.data;
}
