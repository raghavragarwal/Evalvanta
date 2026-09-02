# Evalvanta — Architecture

## 1. Tech Stack

| Layer | Choice | Reasoning |
|---|---|---|
| Frontend | React (Vite) | Fast dev loop, simple SPA fits the linear interview flow |
| Backend | Python + FastAPI | Async, auto-generated OpenAPI docs, strong typing via Pydantic |
| LLM (generation) | Google Gemini API (`gemini-3.6-flash`) | Resume extraction, question generation, session insights — free tier, no card required |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2, local) | Fast, offline, no rate limits, and decouples retrieval quality/cost from whichever LLM provider is generating text |
| Vector DB | ChromaDB (persistent, local) | Zero-infra, embedded, perfect for a single-corpus-per-role RAG setup |
| Relational DB | SQLite + SQLAlchemy | Zero setup; schema is portable to Postgres later (noted as a scaling path in README) |
| Resume parsing | `pypdf` + Gemini for structured extraction | Raw text extraction locally, then Gemini turns it into structured skills/tech/domain JSON |

## 2. High-Level Flow

```
┌─────────────┐   upload resume    ┌──────────────────┐
│   Frontend   │ ─────────────────▶│  POST /candidates │
│  (React)     │   + select role    │  parses resume    │
└─────────────┘                    └────────┬──────────┘
                                             │ Gemini: extract
                                             │ skills/tech/domain
                                             ▼
                                    ┌──────────────────┐
                                    │ Context Builder    │
                                    │ resume + role      │
                                    │ → retrieval queries │
                                    └────────┬──────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  ChromaDB Query    │
                                    │  (role-specific     │
                                    │   knowledge base)   │
                                    └────────┬──────────┘
                                             │ top-k chunks
                                             ▼
                                    ┌──────────────────┐
                                    │ Gemini: Question    │
                                    │ Generation           │
                                    │ (context + resume)  │
                                    └────────┬──────────┘
                                             │
                     ┌───────────────────────┴────────────────────┐
                     ▼                                             ▼
            ┌──────────────────┐                         ┌──────────────────┐
            │  Frontend shows    │◀── answer submitted ───│  SQLite: store    │
            │  question, takes   │────────────────────────▶  Q, A, chunk refs │
            │  answer            │                         │  per session       │
            └──────────────────┘                         └──────────────────┘
                     │  (loop N questions, adapts on prior answer)
                     ▼
            ┌──────────────────────────────┐
            │ Gemini: Session Summary /      │
            │ Insights (strengths, gaps,     │
            │ depth of understanding)        │
            └──────────────────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │  Results view      │
            └──────────────────┘
```

## 3. Backend Module Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, router registration ("Evalvanta")
│   ├── config.py                # env-based settings (pydantic-settings) — Gemini key/model, chunk/session tunables
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models: Candidate, InterviewSession, QAPair, SessionSummary
│   │   ├── session.py           # DB session factory
│   │   └── init_db.py
│   ├── api/
│   │   ├── candidates.py        # POST /api/candidates (upload + role select)
│   │   ├── interview.py         # POST /api/interview/start, POST /api/interview/answer
│   │   └── results.py           # GET /api/results/{session_id}
│   ├── services/
│   │   ├── resume_parser.py     # extract raw text (pypdf) -> Gemini structured extraction
│   │   ├── rag_pipeline.py      # embed query, ChromaDB retrieval
│   │   ├── question_gen.py      # Gemini prompt: context + resume -> question
│   │   ├── summary_gen.py       # Gemini prompt: full transcript -> insights
│   │   └── claude_client.py     # thin wrapper around google-genai SDK (name kept from an earlier
│   │                             # Claude-based version; only this file talks to the LLM provider)
│   ├── ingestion/
│   │   ├── chunker.py            # paragraph-aware chunking with word overlap
│   │   ├── embed_and_store.py    # sentence-transformers -> ChromaDB
│   │   └── run_ingestion.py      # CLI script, run once per role corpus
│   └── schemas.py                # Pydantic request/response models
├── knowledge_base/
│   ├── backend_engineer/         # source .txt files for that role
│   └── ai_ml_engineer/
├── chroma_store/                 # persisted vector DB (gitignored, generated)
├── requirements.txt
└── .env.example
```

## 4. Data Model (SQLite)

- **Candidate**: id, name, role_selected, resume_raw_text, extracted_profile (JSON: skills/technologies/domains/summary), created_at
- **InterviewSession**: id, candidate_id, status (in_progress/completed), questions_planned, created_at, completed_at
- **QAPair**: id, session_id, question_order, question_text, retrieved_chunk_ids (JSON), retrieved_chunk_texts (JSON), answer_text, answered_at, created_at
- **SessionSummary**: id, session_id, summary_text, strengths (JSON), gaps (JSON), overall_assessment, created_at

This gives full traceability: every question is linked back to the exact chunks that grounded it, and every answer is linked to its question — satisfying the "Context → Question → Answer → Storage" requirement explicitly.

## 5. RAG Pipeline Detail

**Ingestion (offline, run once per role, or again whenever `knowledge_base/` changes):**
1. Load each role-specific `.txt` file from `knowledge_base/<role>/`
2. Chunk on paragraph boundaries, target ~220 words per chunk, 40-word overlap between consecutive chunks — never splits mid-sentence, and preserves context across chunk boundaries for conceptual/technical material
3. Embed each chunk locally with `all-MiniLM-L6-v2`
4. Store in a **role-namespaced ChromaDB collection** (`backend_engineer`, `ai_ml_engineer`) with metadata: source file, chunk index

**Retrieval (per question, online):**
1. Context Builder combines: candidate's extracted skills/technologies/domains + selected role + topics already covered this session + (from the second question onward) the candidate's most recent answer → forms a natural-language retrieval query
2. Query embedded locally, top-k (default 4) chunks retrieved from the role's Chroma collection
3. Chunks + resume profile + prior questions passed to Gemini with a structured prompt to generate ONE grounded, non-generic, non-repeating question, returned as JSON (`question`, `topic`)

**Adaptive questioning:** each retrieval query folds in the candidate's previous answer as context, so retrieval — and therefore the next question — drifts toward related depth based on how the conversation is actually going, without needing a separate difficulty-scoring model. This satisfies the "questions may adapt" bonus criterion.

## 6. LLM Integration Notes (Gemini-specific)

A few Gemini-specific details worth knowing if you touch `claude_client.py`:

- **Model**: `gemini-3.6-flash`, set via `GEMINI_MODEL` in `.env`. Gemini model availability shifts over time (an earlier default, `gemini-2.5-flash`, was retired for new users during development) — if generation calls start 404ing, check the [Gemini API model list](https://ai.google.dev/gemini-api/docs/models) for the current recommended flash model.
- **Thinking tokens**: Gemini 3.x models "think" before answering by default, and those thinking tokens are drawn from the same `max_output_tokens` budget as the visible answer. Unlike Gemini 2.5, Gemini 3 models do **not** support `thinking_budget: 0` to disable thinking — attempting it returns a `400 INVALID_ARGUMENT`. The fix used here is to simply budget generously (2000–4096 tokens per call depending on the task) rather than trying to suppress thinking.
- **JSON output**: Gemini doesn't have a strict "JSON mode" enforced at the SDK level in the way this code uses it, so `call_claude_json()` (in `claude_client.py`) instructs the model to return only JSON in the system prompt, then defensively strips markdown code fences and falls back to regex-extracting the first `{...}` block if `json.loads` fails outright.
- **No embeddings endpoint dependency either way**: whether the generation provider is Gemini, Claude, or anything else, embeddings stay local via `sentence-transformers`. This keeps retrieval cost/latency constant regardless of which LLM is swapped in for generation — see `claude_client.py` for the single seam where a provider swap happens.

## 7. API Surface

- `POST /api/candidates` — multipart resume upload + role → returns candidate_id + extracted profile
- `POST /api/interview/start` — candidate_id → creates session, returns first question
- `POST /api/interview/answer` — session_id, question_id, answer_text → stores answer, returns next question (or marks session complete)
- `GET /api/results/{session_id}` — full transcript + generated summary/insights (summary generated lazily on first fetch after completion)
- `GET /api/health` — health check

Full interactive schema at `/docs` once the backend is running.

## 8. Frontend Flow (React)

1. **Upload screen** — resume upload + role dropdown + optional name
2. **Interview screen** — one question at a time, textarea for answer, progress rail showing session position, submit → fetch next question
3. **Results screen** — full Q&A transcript with retrieval chunk-id tags per question, plus summary card (strengths/gaps/overall assessment) generated by Gemini

State handled via a few `useState` hooks in `App.jsx` (no Redux) — the interview flow is strictly linear, so this is a scale-appropriate choice, not an oversight.

## 9. Key Design Decisions to Highlight in README

- Why local embeddings + Gemini generation split (cost/latency/capability reasoning, and how this seam makes the LLM provider swappable)
- Why chunk size/overlap chosen the way it is (context preservation vs. retrieval precision)
- Why SQLite now / Postgres-ready schema for later
- Traceability: chunk_ids + chunk text snapshots stored per question for auditability
- Adaptive questioning via prior-answer-informed retrieval, as the "creativity" extension
- Gemini 3's thinking-token budgeting quirk, and why the fix is generous token ceilings rather than trying to disable thinking

## 10. Known Limitations

- Frontend keeps `session_id`/`question_id` in React state only — a hard page refresh mid-interview loses the UI's place, even though the backend session itself survives and could be resumed with a small `sessionStorage` addition.
- Gemini model names and thinking-mode behavior have moved fast during this project's development; if `claude_client.py` starts erroring on a fresh setup, check current Gemini model availability and thinking-config support before assuming the code is broken.
