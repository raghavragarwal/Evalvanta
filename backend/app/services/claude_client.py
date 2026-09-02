"""
Single point of contact with the LLM (Google Gemini).

Centralizing this (rather than calling the SDK from each service) means the
model name, retry behavior, and JSON-parsing convention live in one place --
and it's easy to swap providers again later without touching resume_parser,
question_gen, or summary_gen.

Note: function names are kept as call_claude / call_claude_json for backward
compatibility with the rest of the codebase, even though the underlying
provider is now Gemini. Rename freely if you'd like -- just update the three
`from app.services.claude_client import ...` lines in services/.
"""
import json
import re

from google import genai

from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)


def call_claude(system: str, user: str, max_tokens: int = 4096) -> str:
    """Single-turn call. Returns the raw text response."""
    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=user,
        config={
            "system_instruction": system,
            "max_output_tokens": max_tokens,
        },
    )
    return response.text or ""


def call_claude_json(system: str, user: str, max_tokens: int = 1024) -> dict:
    """
    Calls the model with an instruction to return ONLY JSON, then parses it.
    Strips markdown code fences defensively in case the model adds them anyway.
    """
    strict_system = (
        system
        + "\n\nRespond with ONLY a valid JSON object. No preamble, no markdown "
        "code fences, no explanation before or after the JSON."
    )
    raw = call_claude(strict_system, user, max_tokens=max_tokens)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: try to locate the first {...} block in the response
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
