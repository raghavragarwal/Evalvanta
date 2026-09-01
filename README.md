# Evalvanta

A RAG-driven system that simulates a structured technical interview. Instead of a fixed question
bank, questions are generated dynamically from a candidate's resume, the selected role, and
grounded content retrieved from a role-specific knowledge base.

## Contents

- [System Architecture](#system-architecture)
- [Setup Instructions](#setup-instructions)
- [Using the real textbooks](#using-the-real-textbooks-instead-of-the-sample-corpus)
- [Key Design Decisions](#key-design-decisions)
- [API Overview](#api-overview)
- [Project Structure](#project-structure)

## System Architecture

```
Frontend (React/Vite)  ──HTTP──▶  Backend (FastAPI)
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                   ▼
              Claude API        ChromaDB (local)      SQLite
         (extraction, question   (role-namespaced      (candidates, sessions,
          generation, summary)    vector collections)   Q&A pairs, summaries)
```

**Flow:** resume upload → Claude extracts a structured profile (skills / technologies / domains)
→ that profile + role + session history builds a retrieval query → ChromaDB returns grounding
chunks from the role's knowledge base → Claude generates one question from that context → answer
is stored → loop until the session's question count is reached → Claude generates a final
structured summary from the full transcript.

See `ARCHITECTURE.md` (if present) or the section below for the deeper module-by-module design.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Google Gemini API key, free — [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (no credit card required)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY

# Ingest the knowledge base into ChromaDB (run once, and again whenever
# knowledge_base/ contents change)
python -m app.ingestion.run_ingestion

# Initialize the SQLite database
python -m app.db.init_db

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is now running at `http://localhost:5173`.

### 3. Try it

Open the frontend, upload a resume (PDF or plain text), pick a role, and start the interview.

## Using the real textbooks instead of the sample corpus

The assignment specifies the provided textbooks (e.g. *Machine Learning* — Tom Mitchell for the
AI/ML role) as the intended knowledge source. This repo ships with a **small original sample
corpus** per role (`backend/knowledge_base/<role>/*.txt`) so ingestion and retrieval work
out of the box without requiring you to source and extract large PDFs first.

To swap in the real textbook(s):

1. Extract the textbook PDF to plain text (e.g. with `pypdf`, or any PDF-to-text tool).
2. Save the `.txt` file(s) into the matching role folder, e.g.
   `backend/knowledge_base/ai_ml_engineer/mitchell_machine_learning.txt`.
3. Re-run `python -m app.ingestion.run_ingestion` — it will chunk, embed, and upsert the new
   content into that role's ChromaDB collection (existing sample chunks stay unless you clear
   the collection first).

No other code changes are needed — the chunking, embedding, and retrieval pipeline is
content-agnostic.

## Key Design Decisions

**Gemini for generation, local embeddings for retrieval.** Generation (resume extraction,
question-writing, assessment) is handled by the Google Gemini API (`gemini-2.5-flash`), chosen
for its free tier. Embeddings are computed locally with `sentence-transformers`
(`all-MiniLM-L6-v2`) rather than via any hosted embeddings API. This is a deliberate split, not
just a cost workaround: retrieval needs fast, cheap, repeatable vector similarity over a fixed
corpus, which a small local model handles well without adding API latency, rate limits, or cost
to every retrieval call — while generation benefits from a stronger hosted model's reasoning
quality. The LLM call is centralized in `app/services/claude_client.py` behind two functions
(`call_claude` / `call_claude_json`), so swapping providers again later (e.g. to Anthropic's
Claude API, or a local model via Ollama) only requires editing that one file.

**Paragraph-aware chunking with overlap.** Knowledge-base text is chunked on paragraph
boundaries (never mid-sentence) targeting ~220 words per chunk, with a 40-word overlap between
consecutive chunks. This preserves context across chunk boundaries for conceptual/technical
material, where a single idea often spans more than one paragraph.

**Role-namespaced vector collections.** Each role gets its own ChromaDB collection rather than
one shared collection filtered by metadata. This keeps retrieval scoped and fast, and makes it
trivial to re-ingest or clear one role's corpus without touching another's.

**Traceability by construction.** Every generated question stores the exact chunk IDs (and a
snapshot of their text) that grounded it, in the `QAPair.retrieved_chunk_ids` /
`retrieved_chunk_texts` columns. The results view surfaces these as tags under each question, so
the full chain — retrieved context → generated question → candidate answer → stored record — is
auditable rather than just "the model said so."

**Lightweight adaptive questioning.** Rather than a full multi-turn adaptive difficulty engine
(out of scope for a 48-hour build), each retrieval query incorporates (a) topics already covered
in the session, so retrieval doesn't keep surfacing near-duplicate chunks, and (b) the
candidate's most recent answer as context, which lets the next question drift toward related
depth based on how the conversation is actually going. This satisfies the assignment's "questions
may adapt" bonus criterion without requiring a separate difficulty-scoring model.

**SQLite now, Postgres-ready schema.** SQLite needs zero setup and is enough for this scope. The
schema is plain SQLAlchemy models with no SQLite-specific types, so switching
`DATABASE_URL` to a Postgres connection string is the only change needed to move to a
production-grade relational store.

**Deliberate simplicity in frontend state.** The interview flow is strictly linear (upload →
interview → results), so state lives in a few `useState` hooks in `App.jsx` rather than a global
state library. This is a scale-appropriate choice, not an oversight — worth calling out
explicitly since "simple" and "unfinished" can look similar from the outside.

## API Overview

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/candidates` | Upload resume + select role → returns extracted profile |
| `POST` | `/api/interview/start` | Start a session for a candidate → returns first question |
| `POST` | `/api/interview/answer` | Submit an answer → returns next question or marks complete |
| `GET` | `/api/results/{session_id}` | Full transcript + generated summary/insights |
| `GET` | `/api/health` | Health check |

Full interactive schema at `/docs` once the backend is running.

## Project Structure

```
backend/
  app/
    main.py                 FastAPI app + router registration
    config.py                Environment-based settings
    schemas.py                Pydantic request/response models
    db/                       SQLAlchemy models + session management
    api/                      candidates.py, interview.py, results.py
    services/                 claude_client, resume_parser, rag_pipeline,
                               question_gen, summary_gen
    ingestion/                chunker, embed_and_store, run_ingestion (CLI)
  knowledge_base/
    backend_engineer/         sample corpus (.txt) -- swap in real textbook here
    ai_ml_engineer/            sample corpus (.txt) -- swap in real textbook here
  chroma_store/                generated at ingestion time (gitignored)
  requirements.txt
  .env.example

frontend/
  src/
    App.jsx                   stage orchestration (upload / interview / results)
    api.js                     backend fetch client
    components/
      UploadScreen.jsx
      InterviewScreen.jsx
      ResultsScreen.jsx
    index.css                  design tokens
  package.json
  vite.config.js
```

## Demo Video

_Add a link to your demo video here before submission._ It should show: resume upload, role
selection, the dynamically generated interview questions, answering the interview, and the final
structured summary with traceable retrieval tags.
