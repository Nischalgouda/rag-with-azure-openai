/**
 * Deterministic mock backend, used by `npm run mock`. It lets the UI be developed, demoed and
 * tested with no Azure resources. It simulates retrieval with word overlap, so its numbers are
 * illustrative, not real model output. The UI labels mock mode clearly.
 *
 * Magic inputs for exercising error states: include "error401", "error429" or "error502".
 */
import { ApiError } from "./errors";
import type { AskParams, AskResult } from "./types";
import type { RankedChunk, SearchMode } from "./schema";

const THRESHOLD = 0.23;
const TOP_K = 4;
const RRF_K = 60;

const CORPUS = [
  { source: "azure_ai_search.md", text: "Azure AI Search is a managed search service. It stores documents in an index and supports full-text keyword search, vector search, and hybrid search that combines both. Hybrid search merges the two result lists using Reciprocal Rank Fusion (RRF)." },
  { source: "azure_ai_search.md", text: "The semantic ranker is an optional feature that re-ranks the top results using a language model, improving relevance for natural-language questions. The Free tier allows one service per subscription with limited storage (50 MB) and up to three indexes." },
  { source: "azure_ai_search.md", text: "Azure OpenAI Service hosts OpenAI models inside Azure. You first create a resource, then create a deployment for each model. Your code calls the deployment name, not the model name. Managed identity is preferred in production because no secret is stored in code." },
  { source: "rag_concepts.md", text: "Retrieval-Augmented Generation (RAG) gives a language model facts it was never trained on. At question time the system retrieves the most relevant chunks of your documents and inserts them into the prompt, so the model answers from that context." },
  { source: "rag_concepts.md", text: "Chunk size is a trade-off. Small chunks give precise matches but may lose surrounding context. Overlap between chunks prevents facts from being cut in half at a boundary. Reduce hallucination: answer only from the context, require citations, and refuse to answer when the best retrieval score is below a threshold." },
  { source: "fastapi_basics.md", text: "FastAPI is a Python web framework for building REST APIs. It uses type hints and Pydantic models to validate request bodies automatically. Raise HTTPException with a status code to return errors; use 502 when an upstream service such as an LLM endpoint fails." },
  { source: "docker_azure_deploy.md", text: "A Dockerfile describes how to build an image. Copy requirements.txt and install dependencies before copying the source code so Docker can cache the slow install layer. Push the image to Azure Container Registry, then run it on Azure Container Apps, which scales to zero." },
  { source: "docker_azure_deploy.md", text: "Never bake secrets into an image. Prefer managed identity. Use Azure Monitor and Application Insights for logs and traces. Track token usage per request because Azure OpenAI is billed per token. Set budget alerts in Cost Management." },
] as const;

const STOP = new Set("a an and are as at be by do does for from how i in is it of on or the to what which why with you your can my".split(" "));
const tokens = (s: string): string[] =>
  (s.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter((w) => !STOP.has(w) && w.length > 1);

function rank(scores: number[]): number[] {
  return scores.map((_, i) => i).sort((a, b) => (scores[b] ?? 0) - (scores[a] ?? 0));
}

function chunkOf(id: number, rankPos: number, cosine: number, stageScore: number): RankedChunk {
  const c = CORPUS[id]!;
  return {
    chunk_id: id,
    source: c.source,
    text_preview: c.text.slice(0, 180) + (c.text.length > 180 ? "…" : ""),
    cosine,
    rank: rankPos,
    stage_score: stageScore,
  };
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });
}

const DAILY_LIMIT = 15;
let questionsAsked = 0;

export async function mockAsk({ question, mode, signal }: AskParams): Promise<AskResult> {
  const started = performance.now();
  questionsAsked += 1;
  await sleep(650, signal);

  const q = question.toLowerCase();
  if (q.includes("error401")) throw new ApiError("auth", "Invalid or missing API key", { status: 401 });
  if (q.includes("error429")) throw new ApiError("rate_limit", "Daily demo limit reached", { status: 429, retryAfterSeconds: 42 });
  if (q.includes("error502")) throw new ApiError("upstream", "Model call failed: endpoint unreachable", { status: 502 });

  const qTokens = new Set(tokens(question));
  const overlap = CORPUS.map((c) => {
    const ct = new Set(tokens(c.text));
    let hits = 0;
    for (const t of qTokens) if (ct.has(t)) hits += 1;
    return hits;
  });
  // Simulated cosine on Azure's scale: unrelated ~0.05-0.15, related ~0.3-0.6.
  // One shared word is coincidence, not relevance, so the boost starts at the second shared term.
  const cosines = overlap.map((hits, i) => {
    const jitter = ((i * 37) % 11) / 200;
    const related = Math.max(0, hits - 1) / Math.max(qTokens.size, 3);
    return Math.min(0.78, 0.06 + jitter + related * 0.75);
  });
  const bm25 = overlap.map((h) => h * 1.7);

  const vectorOrder = rank(cosines);
  const keywordOrder = rank(bm25).filter((i) => (bm25[i] ?? 0) > 0);

  const fusedScore = new Map<number, number>();
  for (const order of [vectorOrder, keywordOrder]) {
    order.forEach((id, pos) => fusedScore.set(id, (fusedScore.get(id) ?? 0) + 1 / (RRF_K + pos + 1)));
  }
  const fusedOrder = [...fusedScore.keys()].sort((a, b) => (fusedScore.get(b) ?? 0) - (fusedScore.get(a) ?? 0));

  const orderFor = (m: SearchMode): number[] =>
    m === "vector" ? vectorOrder : m === "keyword" ? keywordOrder : fusedOrder;
  const picked = orderFor(mode).slice(0, TOP_K);

  const topScore = Math.max(...cosines);
  const refused = topScore < THRESHOLD || picked.length === 0;

  const stages = {
    vector: vectorOrder.map((id, i) => chunkOf(id, i + 1, cosines[id] ?? 0, cosines[id] ?? 0)),
    keyword: keywordOrder.map((id, i) => chunkOf(id, i + 1, cosines[id] ?? 0, bm25[id] ?? 0)),
    fused: picked.map((id, i) => chunkOf(id, i + 1, cosines[id] ?? 0, fusedScore.get(id) ?? cosines[id] ?? 0)),
  };

  const best = picked[0];
  let answer = "I don't know - nothing relevant in the indexed documents.";
  if (!refused && best !== undefined) {
    // Answer with the sentence of the best chunk that shares the most terms with the question.
    const sentences = CORPUS[best]!.text.split(/(?<=\.)\s/);
    const score = (s: string) => tokens(s).filter((t) => qTokens.has(t)).length;
    const top = sentences.reduce((a, b) => (score(b) > score(a) ? b : a), sentences[0]!);
    answer = `${top} [${CORPUS[best]!.source}]`;
  }

  return {
    answer,
    sources: refused
      ? []
      : picked.map((id) => ({ source: CORPUS[id]!.source, score: Number((cosines[id] ?? 0).toFixed(3)), text: CORPUS[id]!.text.slice(0, 200) })),
    top_score: topScore,
    tokens: refused ? 0 : 520 + picked.length * 30 + question.length,
    session_id: "mock-session",
    latency_ms: Math.round(performance.now() - started),
    trace: { mode, threshold: THRESHOLD, decision: refused ? "refused" : "answered", top_score: topScore, stages },
    quota: { limit: DAILY_LIMIT, remaining: Math.max(0, DAILY_LIMIT - questionsAsked) },
  };
}
