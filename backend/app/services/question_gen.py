"""
Question Generation.

Given retrieved knowledge-base chunks + candidate profile + interview history,
asks Claude for exactly one grounded, non-generic interview question.

Explicitly instructed to avoid generic/template questions and to root the
question in the retrieved content, per the assignment's "avoid generic or
template-driven outputs" requirement.
"""
from app.services.claude_client import call_claude_json

QUESTION_SYSTEM_PROMPT = """You are conducting a structured technical interview.
You will be given: the target role, the candidate's extracted background, retrieved
knowledge-base context, and the questions already asked in this session.

Generate exactly ONE new interview question. It must:
- Be grounded in the retrieved context (not generic trivia)
- Be relevant to the target role
- Reflect the candidate's background where it makes sense to probe it (e.g. ask them
  to apply a concept to a technology they listed, or explain a tradeoff related to
  something in their resume)
- NOT repeat or closely resemble any question already asked
- Require conceptual or applied understanding, not a yes/no or one-word answer
- Be answerable in a few sentences by someone with real knowledge of the topic

Return JSON with exactly these keys:
- "question": the question text
- "topic": a short 2-5 word label for the topic this question covers (used to avoid repeats later)
"""


def generate_question(
    role: str,
    extracted_profile: dict,
    retrieved_chunks: list[dict],
    previous_questions: list[str],
) -> dict:
    context_block = "\n\n---\n\n".join(c["text"] for c in retrieved_chunks) or "(no context retrieved)"
    prior_qs = "\n".join(f"- {q}" for q in previous_questions) or "(none yet -- this is the first question)"

    user_prompt = f"""Target role: {role.replace('_', ' ')}

Candidate background summary: {extracted_profile.get('summary', '')}
Candidate skills: {', '.join(extracted_profile.get('skills', []))}
Candidate technologies: {', '.join(extracted_profile.get('technologies', []))}

Retrieved knowledge-base context:
{context_block}

Questions already asked in this session:
{prior_qs}
"""

    result = call_claude_json(system=QUESTION_SYSTEM_PROMPT, user=user_prompt, max_tokens=500)
    return {
        "question": result.get("question", "").strip(),
        "topic": result.get("topic", "").strip(),
    }
