import logging

from openai import AzureOpenAI, OpenAI

from app.config import settings

log = logging.getLogger("rag")


def get_client():
    """Azure OpenAI and OpenAI share the same SDK and the same method names.
    The differences: endpoint, api_version, and that Azure's `model=` is your DEPLOYMENT name."""
    if settings.llm_provider == "azure" or settings.embedding_provider == "azure":
        return AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def chat(messages: list[dict]) -> tuple[str, int]:
    """Returns (answer, total_tokens)."""
    if settings.llm_provider == "azure":
        client = get_client()
        model = settings.azure_openai_chat_deployment
    else:
        client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
        model = settings.llm_model
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0.1,
        max_completion_tokens=settings.max_completion_tokens,
    )
    if resp.choices[0].finish_reason == "length":
        log.warning("Answer was cut off at max_completion_tokens=%s", settings.max_completion_tokens)
    tokens = resp.usage.total_tokens if resp.usage else 0
    return resp.choices[0].message.content or "", tokens
