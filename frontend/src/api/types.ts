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

/** A validated API response plus transport metadata that is not part of the JSON body. */
export type AskResult = AskResponse & { quota?: Quota };
