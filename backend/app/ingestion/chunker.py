"""
Chunking strategy for the knowledge base.

Design choice: paragraph-aware sliding window rather than naive fixed-size
character slicing. We chunk on paragraph boundaries first (so we never split
mid-sentence) and only fall back to fixed-size splitting for individual
paragraphs that are themselves too long. A configurable word-overlap between
consecutive chunks preserves context across chunk boundaries, which matters
for retrieval quality on conceptual/technical text where an idea often spans
multiple paragraphs.
"""

CHUNK_TARGET_WORDS = 220     # ~roughly 300-400 tokens, keeps chunks focused
CHUNK_OVERLAP_WORDS = 40     # preserves continuity across chunk boundaries


def chunk_text(text: str, target_words: int = CHUNK_TARGET_WORDS, overlap_words: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        para_words = para.split()

        # If a single paragraph alone exceeds the target, split it on its own
        if len(para_words) > target_words:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = []
            for i in range(0, len(para_words), target_words - overlap_words):
                chunks.append(" ".join(para_words[i:i + target_words]))
            continue

        if len(current_words) + len(para_words) > target_words:
            chunks.append(" ".join(current_words))
            # start next chunk with overlap from the end of the previous one
            overlap = current_words[-overlap_words:] if overlap_words else []
            current_words = overlap + para_words
        else:
            current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
