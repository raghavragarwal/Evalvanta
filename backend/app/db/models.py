"""
Relational data model.

Design note: QAPair stores `retrieved_chunk_ids` alongside the question text.
This is what makes the pipeline traceable end-to-end -- for any question asked,
we can point back to exactly which knowledge-base chunks grounded it, which the
assignment calls out explicitly ("Ensure traceability of how questions were
generated").
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=True)
    role_selected = Column(String, nullable=False)
    resume_raw_text = Column(Text, nullable=False)
    extracted_profile = Column(JSON, nullable=False, default=dict)  # skills, technologies, domains
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="candidate", cascade="all, delete-orphan")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    status = Column(String, default="in_progress")  # in_progress | completed
    questions_planned = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    candidate = relationship("Candidate", back_populates="sessions")
    qa_pairs = relationship("QAPair", back_populates="session", cascade="all, delete-orphan", order_by="QAPair.question_order")
    summary = relationship("SessionSummary", back_populates="session", uselist=False, cascade="all, delete-orphan")


class QAPair(Base):
    __tablename__ = "qa_pairs"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False)
    question_order = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    retrieved_chunk_ids = Column(JSON, default=list)   # traceability: which KB chunks grounded this question
    retrieved_chunk_texts = Column(JSON, default=list)  # snapshot of chunk content at generation time
    answer_text = Column(Text, nullable=True)
    answered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="qa_pairs")


class SessionSummary(Base):
    __tablename__ = "session_summaries"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    summary_text = Column(Text, nullable=False)
    strengths = Column(JSON, default=list)
    gaps = Column(JSON, default=list)
    overall_assessment = Column(String, nullable=True)  # short label, e.g. "Strong", "Developing", "Needs work"
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="summary")
