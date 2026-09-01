from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExtractedProfile(BaseModel):
    skills: list[str] = []
    technologies: list[str] = []
    domains: list[str] = []
    summary: str = ""


class CandidateCreateResponse(BaseModel):
    candidate_id: str
    role_selected: str
    extracted_profile: ExtractedProfile


class StartInterviewRequest(BaseModel):
    candidate_id: str


class QuestionResponse(BaseModel):
    session_id: str
    question_id: str
    question_order: int
    questions_total: int
    question_text: str
    is_last: bool


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str


class AnswerResponse(BaseModel):
    accepted: bool
    session_complete: bool
    next_question: Optional[QuestionResponse] = None


class QATranscriptItem(BaseModel):
    question_order: int
    question_text: str
    answer_text: Optional[str]
    retrieved_chunk_ids: list[str] = []


class SessionResultsResponse(BaseModel):
    session_id: str
    candidate_id: str
    role_selected: str
    status: str
    transcript: list[QATranscriptItem]
    summary_text: Optional[str] = None
    strengths: list[str] = []
    gaps: list[str] = []
    overall_assessment: Optional[str] = None
    created_at: datetime
