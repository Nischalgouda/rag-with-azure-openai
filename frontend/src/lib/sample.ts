import type { RankedChunk, Trace } from "../api/schema";

/**
 * A fixed, illustrative trace shown on the empty page so the first impression is the product itself.
 * The numbers are modelled on a real run against Azure's text-embedding-3-small (threshold 0.23).
 * The UI labels it "Example"; it is never presented as a live result.
 */
const SOURCES = [
  "azure_ai_search.md",
  "rag_concepts.md",
  "docker_azure_deploy.md",
  "fastapi_basics.md",
  "azure_ai_search.md",
  "rag_concepts.md",
  "docker_azure_deploy.md",
  "fastapi_basics.md",
];
const COSINES = [0.42, 0.31, 0.19, 0.14, 0.12, 0.1, 0.09, 0.07];
const IDS = [0, 4, 6, 5, 1, 3, 7, 2];

const vector: RankedChunk[] = COSINES.map((cosine, i) => ({
  chunk_id: IDS[i]!,
  source: SOURCES[i]!,
  text_preview: "",
  cosine,
  rank: i + 1,
  stage_score: cosine,
}));

export const SAMPLE_QUESTION = "How does hybrid search combine keyword and vector results?";

export const SAMPLE_TRACE: Trace = {
  mode: "hybrid",
  threshold: 0.23,
  decision: "answered",
  top_score: 0.42,
  stages: { vector, keyword: [], fused: vector.slice(0, 2) },
};
