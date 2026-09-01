"""
Context Builder + Retrieval Mechanism.

Turns (resume profile, role, interview history so far) into a retrieval
query, then queries the role's ChromaDB collection for grounding chunks.

The adaptive element: as the session progresses, the query incorporates the
topics already covered (so we don't retrieve near-duplicate chunks for every
question) and, when available, a signal from the candidate's last answer
(covered in question_gen.py's difficulty-adjustment step).
"""
from app.config import settings
from app.ingestion.embed_and_store import query_role_collection


def build_retrieval_query(role: str, extracted_profile: dict, covered_topics: list[str], last_answer: str | None) -> str:
    """Constructs a natural-language query from resume signal + role + session state."""
    skills = ", ".join(extracted_profile.get("skills", [])[:6])
    technologies = ", ".join(extracted_profile.get("technologies", [])[:6])
    domains = ", ".join(extracted_profile.get("domains", [])[:4])

    parts = [f"Role: {role.replace('_', ' ')}."]
    if skills:
        parts.append(f"Candidate skills: {skills}.")
    if technologies:
        parts.append(f"Candidate technologies: {technologies}.")
    if domains:
        parts.append(f"Candidate domain exposure: {domains}.")
    if covered_topics:
        parts.append(f"Avoid repeating these already-covered topics: {', '.join(covered_topics)}.")
    if last_answer:
        # Feeding the previous answer back in lets retrieval drift toward
        # related-but-deeper material when the candidate did well, or toward
        # foundational material when the answer was thin -- a lightweight
        # version of adaptive difficulty.
        parts.append(f"Candidate's most recent answer (for context): {last_answer[:400]}")

    return " ".join(parts)


def retrieve_context(role: str, extracted_profile: dict, covered_topics: list[str], last_answer: str | None) -> list[dict]:
    query = build_retrieval_query(role, extracted_profile, covered_topics, last_answer)
    return query_role_collection(role=role, query_text=query, top_k=settings.retrieval_top_k)
