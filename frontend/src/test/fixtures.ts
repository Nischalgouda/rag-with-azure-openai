import type { AskResponse, RankedChunk } from "../api/schema";

function chunk(id: number, source: string, cosine: number, rank: number, stage = cosine): RankedChunk {
  return { chunk_id: id, source, text_preview: `Preview of chunk ${id}`, cosine, rank, stage_score: stage };
}

export const answered: AskResponse = {
  answer: "Hybrid search merges the two result lists using Reciprocal Rank Fusion (RRF) [azure_ai_search.md].",
  sources: [{ source: "azure_ai_search.md", score: 0.42, text: "Hybrid search merges…" }],
  top_score: 0.42,
  tokens: 589,
  session_id: "s1",
  latency_ms: 4448,
  trace: {
    mode: "hybrid",
    threshold: 0.23,
    decision: "answered",
    top_score: 0.42,
    stages: {
      vector: [chunk(0, "azure_ai_search.md", 0.42, 1), chunk(3, "rag_concepts.md", 0.31, 2), chunk(6, "docker_azure_deploy.md", 0.12, 3)],
      keyword: [chunk(0, "azure_ai_search.md", 0.42, 1, 3.4)],
      fused: [chunk(0, "azure_ai_search.md", 0.42, 1, 0.0328), chunk(3, "rag_concepts.md", 0.31, 2, 0.0161)],
    },
  },
};

export const refused: AskResponse = {
  answer: "I don't know - nothing relevant in the indexed documents.",
  sources: [],
  top_score: 0.15,
  tokens: 0,
  session_id: "s2",
  latency_ms: 700,
  trace: {
    mode: "hybrid",
    threshold: 0.23,
    decision: "refused",
    top_score: 0.15,
    stages: {
      vector: [chunk(6, "docker_azure_deploy.md", 0.15, 1), chunk(1, "azure_ai_search.md", 0.08, 2)],
      keyword: [],
      fused: [chunk(6, "docker_azure_deploy.md", 0.15, 1, 0.0164)],
    },
  },
};

/** A response from today's backend, which does not return a trace yet. */
export const withoutTrace: AskResponse = { ...answered, trace: undefined };
