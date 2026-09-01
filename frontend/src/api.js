const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handle(response) {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* response wasn't JSON */
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function createCandidate({ role, name, resumeFile }) {
  const formData = new FormData();
  formData.append("role", role);
  if (name) formData.append("name", name);
  formData.append("resume", resumeFile);

  const res = await fetch(`${BASE_URL}/api/candidates`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function startInterview(candidateId) {
  const res = await fetch(`${BASE_URL}/api/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id: candidateId }),
  });
  return handle(res);
}

export async function submitAnswer({ sessionId, questionId, answerText }) {
  const res = await fetch(`${BASE_URL}/api/interview/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer_text: answerText,
    }),
  });
  return handle(res);
}

export async function getResults(sessionId) {
  const res = await fetch(`${BASE_URL}/api/results/${sessionId}`);
  return handle(res);
}
