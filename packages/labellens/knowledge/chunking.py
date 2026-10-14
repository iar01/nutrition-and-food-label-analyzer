def chunk_words(text: str, max_words: int = 250, overlap: int = 40) -> list[str]:
    """Split long text into overlapping word windows. Short text stays as one chunk."""
    words = text.split()
    if len(words) <= max_words:
        return [" ".join(words)]
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start : start + max_words]))
        if start + max_words >= len(words):
            break
        start += max_words - overlap
    return chunks
