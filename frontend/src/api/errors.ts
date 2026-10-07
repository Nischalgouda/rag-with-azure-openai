/** A closed set of failure categories, so the UI can render a specific, actionable message. */
export type ApiErrorKind =
  | "network" // request never reached the server
  | "auth" // 401 / 403
  | "rate_limit" // 429
  | "validation" // 422
  | "upstream" // 5xx (e.g. the model endpoint failed)
  | "contract" // the response did not match the schema
  | "unknown";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | null;
  readonly retryAfterSeconds: number | null;

  constructor(
    kind: ApiErrorKind,
    message: string,
    options: { status?: number; retryAfterSeconds?: number } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = options.status ?? null;
    this.retryAfterSeconds = options.retryAfterSeconds ?? null;
  }
}

function kindForStatus(status: number): ApiErrorKind {
  if (status === 401 || status === 403) return "auth";
  if (status === 429) return "rate_limit";
  if (status === 422 || status === 400) return "validation";
  if (status >= 500) return "upstream";
  return "unknown";
}

/** Parse a Retry-After header: either delta-seconds or an HTTP date. */
export function parseRetryAfter(value: string | null, now: number = Date.now()): number | null {
  if (!value) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) return Math.ceil(seconds);
  const date = Date.parse(value);
  if (Number.isNaN(date)) return null;
  return Math.max(0, Math.ceil((date - now) / 1000));
}

/** Turn a non-2xx Response into an ApiError, preferring the server's `detail` message. */
export async function toApiError(res: Response): Promise<ApiError> {
  let detail = res.statusText || `Request failed with status ${res.status}`;
  try {
    const body: unknown = await res.json();
    if (body && typeof body === "object" && "detail" in body) {
      const d = (body as { detail: unknown }).detail;
      if (typeof d === "string") detail = d;
      else if (Array.isArray(d)) detail = "The request was rejected by validation.";
    }
  } catch {
    // Body was not JSON; keep the status text.
  }
  const retryAfterSeconds = parseRetryAfter(res.headers.get("Retry-After"));
  return new ApiError(kindForStatus(res.status), detail, {
    status: res.status,
    ...(retryAfterSeconds !== null ? { retryAfterSeconds } : {}),
  });
}
