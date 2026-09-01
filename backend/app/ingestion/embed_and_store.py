"""
Embeds text chunks locally (sentence-transformers) and stores them in a
role-namespaced ChromaDB collection.

Using a persistent client means ingestion is a one-time offline step -- the
API server just opens the existing store at query time rather than
re-embedding anything.
"""
import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

_embedder: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def get_collection(role: str):
    """Each supported role gets its own Chroma collection -- keeps retrieval
    scoped to that role's corpus rather than filtering a shared collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=role, metadata={"role": role})


def embed_and_store_chunks(role: str, source_name: str, chunks: list[str]) -> int:
    """Embeds a list of chunks and upserts them into the role's collection.
    Returns the number of chunks stored."""
    if not chunks:
        return 0

    embedder = get_embedder()
    collection = get_collection(role)

    embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()
    ids = [f"{source_name}::chunk-{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def query_role_collection(role: str, query_text: str, top_k: int) -> list[dict]:
    """Retrieves the top_k most relevant chunks for a query within a role's collection."""
    embedder = get_embedder()
    collection = get_collection(role)

    query_embedding = embedder.encode([query_text]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    hits = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for _id, doc, meta in zip(ids, docs, metas):
        hits.append({"id": _id, "text": doc, "metadata": meta})
    return hits
