# What is RAG?

Retrieval-Augmented Generation (RAG) gives a language model facts it was never trained on. At question time the system retrieves the most relevant chunks of your documents and inserts them into the prompt, so the model answers from that context instead of from memory.

The pipeline has two phases. Ingestion: load documents, split them into chunks, embed each chunk, and store the vectors. Query: embed the question, find the nearest chunks by cosine similarity, build a prompt with those chunks, and ask the model to answer using only that context.

# Chunking

Chunk size is a trade-off. Small chunks give precise matches but may lose surrounding context. Large chunks keep context but blur several topics into one vector. Overlap between chunks prevents facts from being cut in half at a boundary.

# Reducing hallucination

Instruct the model to answer only from the context, require citations, and refuse to answer when the best retrieval score is below a threshold. Evaluate with a fixed set of test questions and check whether the right chunk was retrieved.
