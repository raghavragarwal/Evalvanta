# Demo Video Script & Pre-Submission Checklist

## Pre-Submission Testing Checklist

Run through this locally before recording, so the demo is a real run, not a rehearsed happy path.

### Setup
- [ ] `backend/.env` has a valid `GEMINI_API_KEY`
- [ ] `python -m app.ingestion.run_ingestion` run — confirm console output shows chunks stored
      for both `backend_engineer` and `ai_ml_engineer`
- [ ] `python -m app.db.init_db` run — confirm `interview_system.db` file appears in `backend/`
- [ ] `uvicorn app.main:app --reload --port 8000` starts with no errors
- [ ] `http://localhost:8000/api/health` returns `{"status": "ok"}`
- [ ] `http://localhost:8000/docs` loads and shows all 4 endpoints

### Functional pass
- [ ] Upload a real resume (PDF) for the **Backend Engineer** role — confirm extracted
      skills/technologies look sane (not empty, not hallucinated)
- [ ] First question is generated and is clearly grounded in one of the backend_engineer
      knowledge_base docs (API design / databases / scalability), not generic
- [ ] Answer a question, confirm the next question doesn't repeat the same topic
- [ ] Complete all 5 questions, confirm results screen shows: summary text, strengths, gaps,
      overall assessment, and a chunk-id tag under each question
- [ ] Repeat the same flow for the **AI/ML Engineer** role with a different resume
- [ ] Try an edge case: upload a very short/sparse resume — confirm the system still produces
      reasonable (if more generic) questions rather than erroring
- [ ] Try an edge case: refresh mid-interview — confirm reasonable behavior (session state is
      server-side, so a session_id in a bookmarked URL could theoretically resume; note this as
      a known limitation if the frontend doesn't currently support resuming after a hard refresh)

### Known limitation to be aware of
The current frontend keeps `session_id` and `question_id` in React state only — a full page
refresh mid-interview loses that state (the backend session still exists, but nothing in the UI
points back to it). If you have time before submission, a small improvement is persisting
`sessionId` to `sessionStorage` on the client so a refresh can recover it. Not required, but
worth mentioning proactively in the README as a known limitation if you don't fix it — reviewers
notice unacknowledged gaps more than acknowledged ones.

---