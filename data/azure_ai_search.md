# Azure AI Search overview

Azure AI Search is a managed search service. It stores documents in an index and supports full-text keyword search, vector search, and hybrid search that combines both. Hybrid search merges the two result lists using Reciprocal Rank Fusion (RRF).

The semantic ranker is an optional feature that re-ranks the top results using a language model, improving relevance for natural-language questions.

The Free tier allows one service per subscription with limited storage (50 MB) and up to three indexes. It is suitable for learning and small demos but has no SLA.

# Azure OpenAI overview

Azure OpenAI Service hosts OpenAI models inside Azure. You first create a resource, then create a deployment for each model, for example gpt-4o-mini for chat or text-embedding-3-small for embeddings. Your code calls the deployment name, not the model name.

Authentication can use an API key or Microsoft Entra ID with managed identity. Managed identity is preferred in production because no secret is stored in code.
