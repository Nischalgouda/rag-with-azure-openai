/**
 * The API contract, as runtime-validated schemas.
 *
 * Every response from the backend is parsed against these schemas at the network boundary.
 * If the backend drifts from the contract, the UI fails loudly with a "contract" error instead
 * of rendering undefined values. The same contract is documented for backend work in
 * docs/api-contract.md.
 */
import { z } from "zod";

export const searchModeSchema = z.enum(["vector", "keyword", "hybrid"]);
export type SearchMode = z.infer<typeof searchModeSchema>;

/** One chunk as ranked by one retrieval stage. */
export const rankedChunkSchema = z.object({
  chunk_id: z.number().int(),
  source: z.string(),
  text_preview: z.string(),
  /** Cosine similarity between the question and this chunk. Always present, for every stage. */
  cosine: z.number(),
  /** 1-based position within this stage's ranking. */
  rank: z.number().int().min(1),
  /** The score this stage ranks by: cosine (vector), BM25 (keyword) or RRF score (fused). */
  stage_score: z.number(),
});
export type RankedChunk = z.infer<typeof rankedChunkSchema>;

export const traceSchema = z.object({
  mode: searchModeSchema,
  /** The refusal threshold in force: refuse when the best cosine is below this. */
  threshold: z.number(),
  decision: z.enum(["answered", "refused"]),
  top_score: z.number(),
  stages: z.object({
    vector: z.array(rankedChunkSchema),
    keyword: z.array(rankedChunkSchema),
    /** The chunks actually placed in the prompt (top-k after fusion). */
    fused: z.array(rankedChunkSchema),
  }),
});
export type Trace = z.infer<typeof traceSchema>;

export const sourceSchema = z.object({
  source: z.string(),
  score: z.number(),
  text: z.string(),
});
export type Source = z.infer<typeof sourceSchema>;

export const askResponseSchema = z.object({
  answer: z.string(),
  sources: z.array(sourceSchema),
  top_score: z.number(),
  tokens: z.number().int(),
  session_id: z.string(),
  latency_ms: z.number(),
  /** Optional until the backend implements it; the UI degrades gracefully without it. */
  trace: traceSchema.optional(),
});
export type AskResponse = z.infer<typeof askResponseSchema>;
