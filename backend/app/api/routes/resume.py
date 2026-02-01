from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_current_user, get_resume_service
from app.api.schemas import ResumeDetail, ResumeUploadResponse
from app.domain.services.resume_service import ResumeService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeUploadResponse:
    logger.info("resume_upload_request", user_id=user_id, filename=file.filename)

    _validate_file(file)
    pdf_bytes = await _read_file(file)

    try:
        resume = resume_service.process_resume_upload(user_id, pdf_bytes)
        background_tasks.add_task(resume_service.generate_and_store_embedding, resume)

        return ResumeUploadResponse(
            id=resume.id,
            user_id=resume.user_id,
            file_path=resume.file_path,
            uploaded_at=datetime.now(timezone.utc),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=ResumeDetail)
async def get_resume(
    user_id: str = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    try:
        resume = resume_service.get_user_resume(user_id)

        return ResumeDetail(
            id=resume.id,
            user_id=resume.user_id,
            file_path=resume.file_path,
            text_preview=resume.text[:500],
            uploaded_at=datetime.now(timezone.utc),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _validate_file(file: UploadFile) -> None:
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported")


async def _read_file(file: UploadFile) -> bytes:
    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    return contents
