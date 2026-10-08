import { z } from "zod";

import { askResponseSchema } from "../api/schema";
import type { AskResult } from "../api/types";
import savedFile from "../data/saved-runs.json";

/**
 * Real responses captured from the live system for the example questions (scripts/capture_saved_runs.py).
 * Replaying them costs nothing, never hits a daily limit, and still works if the shared budget is used up.
 * The file is validated against the API contract at import time, so a stale capture fails loudly.
 */
const fileSchema = z.object({
  generated_at: z.string(),
  mode: z.literal("hybrid"),
  runs: z.record(z.string(), askResponseSchema),
});

const saved = fileSchema.parse(savedFile);

export function getSavedRun(question: string): AskResult | undefined {
  const run = saved.runs[question];
  return run ? { ...run, saved: { at: saved.generated_at } } : undefined;
}

export const savedQuestions: readonly string[] = Object.keys(saved.runs);
