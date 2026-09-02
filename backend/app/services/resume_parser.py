"""
Resume processing: turns an uploaded file into raw text, then asks Claude to
extract a structured profile (skills / technologies / domain exposure).

This structured profile is what later drives retrieval query construction --
per the assignment's "Resume Utilisation" requirement, it should meaningfully
influence topic selection, difficulty, and interview direction.
"""
import io

from pypdf import PdfReader

from app.services.claude_client import call_claude_json

EXTRACTION_SYSTEM_PROMPT = """You are an expert technical recruiter assistant.
Given raw resume text, extract a structured profile.

Return JSON with exactly these keys:
- "skills": list of soft/technical skill names (e.g. "system design", "debugging")
- "technologies": list of concrete tools/languages/frameworks/platforms mentioned
- "domains": list of domain areas of exposure (e.g. "distributed systems", "NLP", "fintech")
- "summary": a 2-3 sentence neutral summary of the candidate's background and seniority level

Only include items that are actually supported by the resume text. Do not invent skills."""


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    """Extracts raw text from an uploaded PDF or plain-text resume."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    # Fallback: treat as plain text (.txt, .md, or unknown -> best effort decode)
    return file_bytes.decode("utf-8", errors="ignore").strip()


def extract_structured_profile(resume_text: str) -> dict:
    """Calls Claude to turn raw resume text into a structured skills/tech/domain profile."""
    if not resume_text.strip():
        return {"skills": [], "technologies": [], "domains": [], "summary": ""}

    result = call_claude_json(
        system=EXTRACTION_SYSTEM_PROMPT,
        user=f"Resume text:\n\n{resume_text[:8000]}",  # guard against extremely long resumes
        max_tokens=3000,
    )
    # Defensive defaults in case Claude omits a key
    return {
        "skills": result.get("skills", []),
        "technologies": result.get("technologies", []),
        "domains": result.get("domains", []),
        "summary": result.get("summary", ""),
    }
