from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import candidates, interview, results
from app.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Evalvanta",
    description="RAG-driven dynamic technical interview backend.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router)
app.include_router(interview.router)
app.include_router(results.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
