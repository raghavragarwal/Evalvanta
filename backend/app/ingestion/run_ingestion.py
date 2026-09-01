"""
Offline ingestion entrypoint.

Run once (and again any time the knowledge_base/ contents change):
    python -m app.ingestion.run_ingestion

Walks backend/knowledge_base/<role>/*.txt, chunks each file, embeds the
chunks, and stores them in that role's ChromaDB collection.

To swap in the real textbooks: drop extracted .txt files into the matching
role folder (e.g. knowledge_base/ai_ml_engineer/mitchell_machine_learning.txt)
and re-run this script. See README for PDF -> text extraction notes.
"""
import pathlib

from app.config import settings
from app.ingestion.chunker import chunk_text
from app.ingestion.embed_and_store import embed_and_store_chunks

KB_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent / "knowledge_base"


def ingest_role(role: str) -> None:
    role_dir = KB_ROOT / role
    if not role_dir.exists():
        print(f"  [skip] no knowledge_base folder found for role '{role}' ({role_dir})")
        return

    total_chunks = 0
    for file_path in sorted(role_dir.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text)
        stored = embed_and_store_chunks(role=role, source_name=file_path.stem, chunks=chunks)
        total_chunks += stored
        print(f"  [{role}] {file_path.name}: {len(chunks)} chunks -> stored {stored}")

    print(f"  [{role}] total chunks stored: {total_chunks}")


def main():
    print(f"Ingesting knowledge base from: {KB_ROOT}")
    for role in settings.supported_roles:
        print(f"\nRole: {role}")
        ingest_role(role)
    print("\nIngestion complete.")


if __name__ == "__main__":
    main()
