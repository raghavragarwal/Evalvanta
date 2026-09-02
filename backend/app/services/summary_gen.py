"""
Final Output: structured summary + basic insights on the interview session.
"""
from app.services.claude_client import call_claude_json

SUMMARY_SYSTEM_PROMPT = """You are a technical interview assessor. You will be given the
full transcript of a structured interview: the role, the questions asked, and the
candidate's answers.

Produce an honest, specific assessment. Avoid vague praise -- ground every point in
something the candidate actually said or failed to address.

Return JSON with exactly these keys:
- "summary_text": a 3-5 sentence overall narrative summary of the session
- "strengths": list of 2-5 short, specific strengths demonstrated (empty list if none clear)
- "gaps": list of 2-5 short, specific gaps or areas needing development (empty list if none clear)
- "overall_assessment": one of "Strong", "Solid", "Developing", "Needs Work"
"""


def generate_session_summary(role: str, transcript: list[dict]) -> dict:
    transcript_block = "\n\n".join(
        f"Q{i+1}: {item['question_text']}\nA{i+1}: {item['answer_text'] or '(no answer given)'}"
        for i, item in enumerate(transcript)
    )

    user_prompt = f"""Role: {role.replace('_', ' ')}

Interview transcript:
{transcript_block}
"""

    result = call_claude_json(system=SUMMARY_SYSTEM_PROMPT, user=user_prompt, max_tokens=3000)
    return {
        "summary_text": result.get("summary_text", ""),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "overall_assessment": result.get("overall_assessment", ""),
    }
