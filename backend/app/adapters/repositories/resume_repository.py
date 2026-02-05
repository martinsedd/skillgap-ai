from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.model.resume import Resume
from app.domain.ports.repositories import ResumeRepository
from app.infrastructure.database.models import ResumeModel
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SQLAlchemyResumeRepository(ResumeRepository):
    """SQLAlchemy implementation of ResumeRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, resume: Resume) -> Resume:
        logger.info("saving_resume", resume_id=resume.id, user_id=resume.user_id)

        existing = self._find_model_by_id(resume.id)

        if existing:
            self._update_model(existing, resume)
        else:
            self._create_model(resume)

        self.session.commit()
        logger.info("resume_saved", resume_id=resume.id)
        return resume

    def find_by_id(self, resume_id: str) -> Resume | None:
        model = self._find_model_by_id(resume_id)
        return self._to_domain(model) if model else None

    def find_by_user_id(self, user_id: str) -> Resume | None:
        model = (
            self.session.query(ResumeModel)
            .filter(ResumeModel.user_id == user_id)
            .order_by(ResumeModel.uploaded_at.desc())
            .first()
        )
        return self._to_domain(model) if model else None

    def delete(self, resume_id: str) -> bool:
        model = self._find_model_by_id(resume_id)
        if not model:
            return False

        self.session.delete(model)
        self.session.commit()
        logger.info("resume_deleted", resume_id=resume_id)
        return True

    def _find_model_by_id(self, resume_id: str) -> ResumeModel | None:
        return self.session.query(ResumeModel).filter(ResumeModel.id == resume_id).first()

    def _create_model(self, resume: Resume) -> ResumeModel:
        model = ResumeModel(
            id=resume.id,
            user_id=resume.user_id,
            file_path=resume.file_path,
            extracted_text=resume.text,
            pinecone_id=resume.pinecone_id,
            uploaded_at=datetime.now(timezone.utc),
        )
        self.session.add(model)
        return model

    def _update_model(self, model: ResumeModel, resume: Resume) -> None:
        setattr(model, "file_path", resume.file_path)
        setattr(model, "extracted_text", resume.text)
        setattr(model, "pinecone_id", resume.pinecone_id)
        setattr(model, "uploaded_at", datetime.now(timezone.utc))

    def _to_domain(self, model: ResumeModel) -> Resume:
        return Resume(
            id=str(model.id),
            user_id=str(model.user_id),
            text=str(model.extracted_text),
            file_path=str(model.file_path),
            pinecone_id=str(model.pinecone_id),
        )
