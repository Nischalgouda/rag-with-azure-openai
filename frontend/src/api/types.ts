import type { AskResponse, SearchMode } from "./schema";

export interface AskParams {
  question: string;
  mode: SearchMode;
  apiKey?: string | undefined;
  sessionId?: string | undefined;
  signal?: AbortSignal | undefined;
}

/** The caller's daily allowance, read from the X-Daily-Limit / X-Daily-Remaining response headers. */
export interface Quota {
  limit: number;
  remaining: number;
}

/**
 * A validated API response plus metadata that is not part of the JSON body:
 * `quota` comes from response headers; `saved` marks a replayed real run (no request was made).
 */
export type AskResult = AskResponse & { quota?: Quota; saved?: { at: string } };
