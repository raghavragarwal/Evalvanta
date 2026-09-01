# Evalvanta — Architecture

## 1. Tech Stack

| Layer | Choice | Reasoning |
|---|---|---|
| Frontend | React (Vite) | Fast dev loop, simple SPA fits the linear interview flow |
| Backend | Python + FastAPI | Async, auto-generated OpenAPI docs, strong typing via Pydantic |
| LLM (generation) | Claude API (Anthropic) | Resume extraction, question generation, session insights |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2, local) | Claude has no embeddings endpoint; local model = free, fast, offline, no rate limits for a 48h build |
| Vector DB | ChromaDB (persistent, local) | Zero-infra, embedded, perfect for a single-corpus-per-role RAG setup |
| Relational DB | SQLite + SQLAlchemy | Zero setup; schema is portable to Postgres later (noted as a scaling path in README) |
| Resume parsing | `pypdf` / `python-docx` + Claude for structured extraction | Raw text extraction locally, then Claude turns it into structured skills/tech/domain JSON |

## 2. High-Level Flow

```
┌─────────────┐   upload resume    ┌──────────────────┐
│   Frontend   │ ─────────────────▶│  POST /candidates │
│  (React)     │   + select role    │  parses resume    │
└─────────────┘                    └────────┬──────────┘
                                             │ Claude: extract
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
                                    │ Claude: Question    │
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
                     │  (loop N questions, optionally adaptive)
                     ▼
            ┌──────────────────────────────┐
            │ Claude: Session Summary /      │
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
│   ├── main.py                 # FastAPI app, router registration
│   ├── config.py                # env-based settings (pydantic-settings)
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models: Candidate, Session, QAPair
│   │   ├── session.py           # DB session factory
│   │   └── init_db.py
│   ├── api/
│   │   ├── candidates.py        # POST /candidates (upload + role select)
│   │   ├── interview.py         # POST /interview/next, POST /interview/answer
│   │   └── results.py           # GET /results/{session_id}
│   ├── services/
│   │   ├── resume_parser.py     # extract raw text (pypdf) -> Claude structured extraction
│   │   ├── rag_pipeline.py      # embed query, ChromaDB retrieval
│   │   ├── question_gen.py      # Claude prompt: context + resume -> question
│   │   ├── summary_gen.py       # Claude prompt: full transcript -> insights
│   │   └── claude_client.py     # thin wrapper around Anthropic SDK
│   ├── ingestion/
│   │   ├── chunker.py            # role-textbook chunking (semantic/paragraph-based)
│   │   ├── embed_and_store.py    # sentence-transformers -> ChromaDB
│   │   └── run_ingestion.py      # CLI script, run once per role corpus
│   └── schemas.py                # Pydantic request/response models
├── knowledge_base/
│   ├── backend_engineer/         # source PDFs/text for that role
│   └── ai_ml_engineer/
├── chroma_store/                 # persisted vector DB (gitignored, generated)
├── requirements.txt
└── .env.example
```

## 4. Data Model (SQLite)

- **Candidate**: id, name, role_selected, resume_raw_text, extracted_skills (JSON), created_at
- **InterviewSession**: id, candidate_id, status (in_progress/completed), created_at
- **QAPair**: id, session_id, question_text, retrieved_chunk_ids (JSON), answer_text, question_order, created_at
- **SessionSummary**: id, session_id, summary_text, strengths (JSON), gaps (JSON), created_at

This gives full traceability: every question is linked back to the chunks that grounded it, and every answer is linked to its question — satisfying the "Context → Question → Answer → Storage" requirement explicitly.

## 5. RAG Pipeline Detail

**Ingestion (offline, run once per role):**
1. Load role-specific textbook PDF (Tom Mitchell for AI/ML, etc.)
2. Chunk by paragraph/section with overlap (~500 tokens, 50-token overlap) to preserve context across boundaries
3. Embed each chunk with `all-MiniLM-L6-v2`
4. Store in a **role-namespaced ChromaDB collection** (`backend_engineer`, `ai_ml_engineer`) with metadata: source page, chunk index

**Retrieval (per question, online):**
1. Context Builder combines: candidate's extracted skills + selected role + (optionally) previous Q&A in session → forms a natural-language retrieval query
2. Query embedded locally, top-k (e.g. 4) chunks retrieved from the role's Chroma collection
3. Chunks + resume snippet passed to Claude with a structured prompt to generate ONE grounded, non-generic question

**Adaptive extension (optional, for stronger submission):** after each answer, feed the answer back into the next retrieval query so topic difficulty/direction shifts based on how well the candidate is doing — this satisfies the "questions may adapt" bonus criterion.

## 6. API Surface (illustrative, not final)

- `POST /api/candidates` — multipart resume upload + role → returns candidate_id + extracted profile
- `POST /api/interview/start` — candidate_id → creates session, returns first question
- `POST /api/interview/answer` — session_id, question_id, answer_text → stores answer, returns next question (or "complete")
- `GET /api/results/{session_id}` — full transcript + generated summary/insights

## 7. Frontend Flow (React)

1. **Upload screen** — resume upload + role dropdown
2. **Interview screen** — one question at a time, textarea for answer, progress indicator, submit → fetch next question
3. **Results screen** — full Q&A transcript + summary card (strengths/gaps) generated by Claude

State handled via a simple `sessionId` in React context/local component state (no need for Redux at this scale — worth noting as a deliberate simplicity choice in the README).

## 8. Key Design Decisions to Highlight in README

- Why local embeddings + Claude generation split (cost/latency/capability reasoning)
- Why chunk size/overlap chosen the way it is (context preservation vs. retrieval precision)
- Why SQLite now / Postgres-ready schema for later
- Traceability: chunk_ids stored per question for auditability
- Adaptive questioning as the "creativity" extension

## 9. Build Order (for the 48h window)

1. Backend skeleton + DB models + env config
2. Ingestion script — chunk + embed + store one role's textbook into Chroma (prove RAG works standalone)
3. Resume parsing + extraction endpoint
4. Question generation endpoint wired to retrieval
5. Interview loop endpoints + storage
6. Summary generation endpoint
7. Frontend: upload → interview → results
8. README + demo video last
