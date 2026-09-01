from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Candidate
from app.db.session import get_db
from app.schemas import CandidateCreateResponse, ExtractedProfile
from app.services.resume_parser import extract_text_from_upload, extract_structured_profile

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("", response_model=CandidateCreateResponse)
async def create_candidate(
    role: str = Form(...),
    name: str | None = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if role not in settings.supported_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported role '{role}'. Supported roles: {settings.supported_roles}",
        )

    file_bytes = await resume.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    raw_text = extract_text_from_upload(resume.filename or "resume.txt", file_bytes)
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the uploaded resume.")

    profile = extract_structured_profile(raw_text)

    candidate = Candidate(
        name=name,
        role_selected=role,
        resume_raw_text=raw_text,
        extracted_profile=profile,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return CandidateCreateResponse(
        candidate_id=candidate.id,
        role_selected=candidate.role_selected,
        extracted_profile=ExtractedProfile(**profile),
    )
