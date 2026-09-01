from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Candidate, InterviewSession, QAPair
from app.db.session import get_db
from app.schemas import AnswerRequest, AnswerResponse, QuestionResponse, StartInterviewRequest
from app.services.question_gen import generate_question
from app.services.rag_pipeline import retrieve_context

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _generate_next_question(db: Session, session: InterviewSession, candidate: Candidate) -> QAPair:
    """Runs one full retrieval -> generation cycle and persists the resulting question."""
    previous_qas = session.qa_pairs
    covered_topics = [qa.question_text[:60] for qa in previous_qas]  # lightweight topic memory
    last_answer = previous_qas[-1].answer_text if previous_qas and previous_qas[-1].answer_text else None

    chunks = retrieve_context(
        role=candidate.role_selected,
        extracted_profile=candidate.extracted_profile,
        covered_topics=covered_topics,
        last_answer=last_answer,
    )

    generated = generate_question(
        role=candidate.role_selected,
        extracted_profile=candidate.extracted_profile,
        retrieved_chunks=chunks,
        previous_questions=[qa.question_text for qa in previous_qas],
    )

    qa = QAPair(
        session_id=session.id,
        question_order=len(previous_qas) + 1,
        question_text=generated["question"],
        retrieved_chunk_ids=[c["id"] for c in chunks],
        retrieved_chunk_texts=[c["text"] for c in chunks],
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa


def _to_question_response(session: InterviewSession, qa: QAPair) -> QuestionResponse:
    return QuestionResponse(
        session_id=session.id,
        question_id=qa.id,
        question_order=qa.question_order,
        questions_total=session.questions_planned,
        question_text=qa.question_text,
        is_last=qa.question_order >= session.questions_planned,
    )


@router.post("/start", response_model=QuestionResponse)
def start_interview(payload: StartInterviewRequest, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    session = InterviewSession(
        candidate_id=candidate.id,
        status="in_progress",
        questions_planned=settings.questions_per_session,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    qa = _generate_next_question(db, session, candidate)
    return _to_question_response(session, qa)


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerRequest, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    qa = db.get(QAPair, payload.question_id)
    if not qa or qa.session_id != session.id:
        raise HTTPException(status_code=404, detail="Question not found for this session.")
    if qa.answer_text is not None:
        raise HTTPException(status_code=409, detail="This question has already been answered.")

    qa.answer_text = payload.answer_text
    qa.answered_at = datetime.utcnow()
    db.commit()

    if len(session.qa_pairs) >= session.questions_planned:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()
        return AnswerResponse(accepted=True, session_complete=True, next_question=None)

    candidate = db.get(Candidate, session.candidate_id)
    next_qa = _generate_next_question(db, session, candidate)
    return AnswerResponse(
        accepted=True,
        session_complete=False,
        next_question=_to_question_response(session, next_qa),
    )
