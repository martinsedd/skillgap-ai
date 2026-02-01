import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class InterviewState(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class JobSource(str, enum.Enum):
    ADZUNA = "adzuna"
    REMOTEOK = "remoteok"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)


class ResumeModel(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=False)
    pinecone_id = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, nullable=False)
    source = Column(Enum(JobSource), nullable=False)
    dedup_hash = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(String, nullable=False)
    url = Column(String, nullable=False)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    pinecone_id = Column(String, nullable=False)
    extracted_skills = Column(JSONB, nullable=True)


class InterviewSessionModel(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    state = Column(Enum(InterviewState), nullable=False, default=InterviewState.DRAFT)
    conversation_history = Column(JSONB, nullable=False, default=dict)
    overall_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
