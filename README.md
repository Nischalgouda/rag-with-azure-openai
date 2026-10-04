# RAG with Azure OpenAI

A learning project: a Retrieval-Augmented Generation (RAG) API built from first principles, then moved onto **Azure OpenAI** (chat + embeddings) with an optional **Azure AI Search** backend.

I built the retrieval layer by hand first (chunking, embeddings, cosine similarity, BM25, Reciprocal Rank Fusion) so I understand what the managed Azure services abstract away. The project was built together with Claude as a pair-programming partner; every design decision below is something I can explain and change.

## How it works

```mermaid
flowchart LR
    subgraph Ingest
        D[.md / .txt docs] --> C[Chunk + overlap] --> E1[Embed] --> S[(Vector store)]
    end
    subgraph Ask
        Q[Question] --> E2[Embed] --> R[Hybrid retrieval<br/>vector + BM25 + RRF]
        S --> R
        R --> G{Best similarity<br/>above threshold?}
        G -- no --> N["I don't know"]
        G -- yes --> P[Prompt: context-only + cite sources] --> L[Azure OpenAI chat] --> A[Answer + sources]
    end
    A --> DB[(SQLite: tokens, latency, session)]
```

## Features

- **FastAPI** service: `POST /ingest`, `POST /ask`, `GET /usage`, `GET /health`
- **Swappable providers** via `.env`: Azure OpenAI or a free local setup (fastembed embeddings, Ollama/any OpenAI-compatible chat)
- **Hybrid search**: vector + BM25 keyword, fused with Reciprocal Rank Fusion
- **Hallucination guardrail**: refuses to answer (without calling the LLM) when retrieval is weak
- **Evaluation harness** (`python -m eval.run_eval`): hit@k per search mode and refusal accuracy
- **Usage logging** to SQLite: tokens, latency, session id
- **Azure AI Search backend** (`VECTOR_STORE=azure_search`): managed vector + keyword index, optional semantic ranker (verified end to end against a live Free-tier service)
- Tests (chat model faked; embeddings use the configured provider), Dockerfile

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then fill in your values
pytest -q
python -m eval.run_eval
uvicorn app.main:app --reload   # http://localhost:8000/docs
```

Then `POST /ingest` (indexes `data/`) and `POST /ask` with `{"question": "..."}`.

### Configuration (`.env`)

| Variable | Meaning |
|---|---|
| `EMBEDDING_PROVIDER` | `local` or `azure` |
| `LLM_PROVIDER` | `openai_compatible` (e.g. Ollama) or `azure` |
| `AZURE_OPENAI_ENDPOINT` / `_API_KEY` | From the Azure OpenAI resource |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Your chat **deployment name** (e.g. `gpt-4.1-mini`) |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | e.g. `text-embedding-3-small` |
| `VECTOR_STORE` | `local` (numpy) or `azure_search` |
| `MIN_SCORE` | Refusal threshold. **Depends on the embedding model** (see below) |
| `MAX_COMPLETION_TOKENS` | Per-answer cap |

## Project layout

```
app/
  chunking.py      overlapping chunker
  embeddings.py    local or Azure embeddings
  vectorstore.py   numpy cosine search (the "by hand" version)
  keyword.py       BM25
  azure_search.py  Azure AI Search index + hybrid query
  rag.py           ingest(), retrieve() (hybrid + RRF), answer() with guardrail
  llm.py           Azure/OpenAI client, answer-length cap
  db.py            SQLite usage log
  main.py          FastAPI app
eval/              retrieval evaluation (questions.json, run_eval.py)
tests/             unit + API tests (chat model faked)
data/              sample documents
```

## What I learned (real issues hit while building)

![Refusal threshold by embedding model](docs/threshold-by-embedding-model.png)

- **A similarity threshold is specific to the embedding model.** The local `bge-small` model separated off-topic from answerable questions around 0.52; Azure `text-embedding-3-small` scores on a different scale and needed ~0.23. My first guess (0.35) failed the eval's refusal check, which is how I found it. Always calibrate from data and re-calibrate when you change the model.
- **Models get retired.** `gpt-4o-mini` (2024-07-18) failed to deploy with `ServiceModelDeprecated`; I switched to `gpt-4.1-mini`. Check lifecycle dates.
- **Quota is per subscription, region, model and deployment type.** A new subscription showed 0 TPM for some combinations; switching deployment type fixed it.
- **TPM vs `max_completion_tokens`:** TPM is a per-deployment, per-minute limit shared by every call to that deployment (input + output). `max_completion_tokens` is a per-call cap on the answer; hitting it cuts the answer off (`finish_reason="length"`) rather than raising an error.
- **Evaluate retrieval separately from generation.** If the right chunk isn't retrieved, no prompt fixes it.

## Evaluation results (Azure AI Search + Azure OpenAI embeddings, 12 answerable + 3 off-topic questions)

| Mode | hit@1 | hit@3 | Off-topic refused |
|---|---|---|---|
| vector | 9/12 | 12/12 | 3/3 |
| keyword | 11/12 | 12/12 | 3/3 |
| hybrid | 11/12 | 12/12 | 3/3 |

On a corpus of only 8 chunks this is weak evidence: hybrid helps at k=1 but all modes converge at k=3. A larger, messier document set is the next step to see a real difference.

## Limitations and next steps

- The sample corpus is tiny (8 chunks), so differences between search modes are weak evidence; the eval set should grow with realistic documents.
- Auth: API keys only for now; next is Microsoft Entra ID / managed identity.
- Usage logging is SQLite; production would use PostgreSQL and Application Insights.
- Not yet done: PDF ingestion (Document Intelligence), conversation memory, streaming, CI/CD, Azure Container Apps deployment.


