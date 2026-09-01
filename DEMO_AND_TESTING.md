# Demo Video Script & Pre-Submission Checklist

## Part 1 — Pre-Submission Testing Checklist

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

## Part 2 — Demo Video Script (aim for 4–6 minutes)

### 0:00–0:30 — Framing
"This is an AI-powered candidate screening system. Instead of a fixed question bank, it builds
a technical interview dynamically — the questions come from a RAG pipeline that combines the
candidate's resume with a role-specific knowledge base."

Show the architecture diagram from `ARCHITECTURE.md` or `README.md` on screen for ~10 seconds
while you say this — gives reviewers the mental model before they watch the UI.

### 0:30–1:00 — Ingestion (prove the RAG side works, not just the UI)
Run `python -m app.ingestion.run_ingestion` on screen (or show terminal output from an earlier
run). Say: "The knowledge base is chunked paragraph-aware with overlap, embedded locally, and
stored in role-specific ChromaDB collections — one for backend engineering, one for AI/ML."

### 1:00–1:30 — Upload & extraction
Upload a real resume, select a role. When the extracted profile appears (or once the first
question loads), say what got extracted: "You can see it pulled out these skills and
technologies from the resume — that's what drives the retrieval query for the first question."

### 1:30–3:30 — Interview loop
Answer 2–3 questions on camera. For at least one, explicitly say: "Notice this question is about
[topic] — that's grounded in the [chunk topic] content, not a generic interview question." Point
at the progress rail to show session continuity.

### 3:30–4:30 — Results & traceability
Show the final results screen. Call out: "Each question has these tags underneath — those are
the actual knowledge-base chunk IDs that were retrieved and used to generate that question. So
the whole pipeline — context, question, answer, storage — is traceable, not a black box."

Read a snippet of the generated summary and point at the strengths/gaps.

### 4:30–5:00 — Close
"Backend is FastAPI with SQLite for session storage, frontend is React. Full setup and design
rationale — including why embeddings are local while generation uses Claude — are in the
README." End on the repo or README on screen.

### Recording tips
- Do one full un-cut take of the functional pass instead of stitching cuts — a live end-to-end
  run is more convincing than an edited one, and matches "demonstrate the working system
  end-to-end" from the assignment brief.
- Keep the terminal visible at least once (ingestion or server startup) — it's easy proof this
  isn't a static mockup.
- If a question or summary comes back oddly (Claude output can vary), it's fine to keep it in —
  a resilient system handling an imperfect answer often demonstrates more than a cherry-picked
  perfect run.
