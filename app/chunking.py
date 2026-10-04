def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, preferring to cut at paragraph/sentence ends.

    Why chunk at all? Embedding a whole document blurs many topics into one vector,
    and the LLM context window is limited. Why overlap? So a fact that straddles a
    boundary still appears whole in at least one chunk.
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Try to end on a paragraph break, then a sentence end, within the back half.
            window_start = start + size // 2
            for sep in ("\n\n", ". ", "\n"):
                cut = text.rfind(sep, window_start, end)
                if cut != -1:
                    end = cut + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
