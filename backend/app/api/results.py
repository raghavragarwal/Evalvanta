from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Candidate, InterviewSession, SessionSummary
from app.db.session import get_db
from app.schemas import QATranscriptItem, SessionResultsResponse
from app.services.summary_gen import generate_session_summary

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/{session_id}", response_model=SessionResultsResponse)
def get_results(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    candidate = db.get(Candidate, session.candidate_id)

    transcript = [
        QATranscriptItem(
            question_order=qa.question_order,
            question_text=qa.question_text,
            answer_text=qa.answer_text,
            retrieved_chunk_ids=qa.retrieved_chunk_ids or [],
        )
        for qa in session.qa_pairs
    ]

    summary_row = session.summary
    if summary_row is None and session.status == "completed":
        # Lazily generate the summary the first time results are requested
        generated = generate_session_summary(
            role=candidate.role_selected,
            transcript=[qa.__dict__ for qa in session.qa_pairs],
        )
        summary_row = SessionSummary(
            session_id=session.id,
            summary_text=generated["summary_text"],
            strengths=generated["strengths"],
            gaps=generated["gaps"],
            overall_assessment=generated["overall_assessment"],
        )
        db.add(summary_row)
        db.commit()
        db.refresh(summary_row)

    return SessionResultsResponse(
        session_id=session.id,
        candidate_id=candidate.id,
        role_selected=candidate.role_selected,
        status=session.status,
        transcript=transcript,
        summary_text=summary_row.summary_text if summary_row else None,
        strengths=summary_row.strengths if summary_row else [],
        gaps=summary_row.gaps if summary_row else [],
        overall_assessment=summary_row.overall_assessment if summary_row else None,
        created_at=session.created_at,
    )
