from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    embedding_provider: str = "local"  # local | azure
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"

    llm_provider: str = "openai_compatible"  # openai_compatible | azure
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.2"

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    vector_store: str = "local"  # local | azure_search
    search_endpoint: str = ""    # https://<name>.search.windows.net
    search_api_key: str = ""
    search_index_name: str = "rag-chunks"
    use_semantic_ranker: bool = False  # Free tier includes a monthly quota of semantic queries

    chunk_size: int = 800     # characters per chunk
    chunk_overlap: int = 150   # characters shared between neighbouring chunks
    max_completion_tokens: int = 600  # per-answer cap (app-level); TPM is the separate Azure-side limit
    top_k: int = 4
    search_mode: str = "hybrid"  # vector | keyword | hybrid
    # Below this best-cosine we refuse instead of guessing. Calibrated for bge-small on
    # eval/questions.json (off-topic max 0.46, answerable min 0.60). Re-tune per embedding model.
    min_score: float = 0.52

    index_dir: str = "index"
    db_path: str = "usage.db"

    # --- Public-demo behaviour. Off by default so a fork runs frictionless on localhost. ---
    demo_mode: bool = False        # True on the public deployment: limits on, /ingest and /usage admin-only
    demo_enabled: bool = True      # kill switch: False makes /ask return 503 immediately
    admin_key_names: str = "admin"  # comma-separated key owners treated as admins in demo mode
    daily_token_budget: int = 150_000   # global cap on model tokens per UTC day (stops runaway cost)
    anon_daily_questions: int = 15      # per client IP per UTC day
    keyed_daily_questions: int = 200    # per API key per UTC day
    anon_burst: int = 4                 # token bucket capacity (anonymous)
    anon_refill_seconds: float = 15.0   # seconds to earn one more request (anonymous)
    keyed_burst: int = 10
    keyed_refill_seconds: float = 4.0
    static_dir: str = "static"          # built frontend served by app.server in the container
    # How many reverse proxies sit in front of the app. 0 = trust no forwarded headers (local dev).
    # On Azure Container Apps the platform ingress is one hop, so the visitor's address is the LAST
    # X-Forwarded-For entry (the one our own proxy appended). Earlier entries can be forged by the client.
    trusted_proxy_hops: int = 0


settings = Settings()
