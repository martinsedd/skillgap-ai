from datetime import datetime

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    id: str
    user_id: str
    file_path: str
    uploaded_at: datetime
    message: str = "Resume uploaded and processed successfully"


class ResumeDetail(BaseModel):
    id: str
    user_id: str
    file_path: str
    text_preview: str = Field(..., description="First 500 characters of resume text")
    uploaded_at: datetime


class JobSkills(BaseModel):
    required: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    seniority_level: str | None = None


class JobDetail(BaseModel):
    id: str
    title: str
    company: str
    description: str
    url: str
    location: str | None = None
    salary: str | None = None
    source: str
    posted_at: datetime | None = None
    fetched_at: datetime | None = None


class JobWithSkills(JobDetail):
    skills: JobSkills | None = None


class JobMatchResult(BaseModel):
    job: JobDetail
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Vector similarity score")
    skill_match_score: float = Field(..., ge=0.0, le=1.0, description="Skill overlap score")
    combined_score: float = Field(..., ge=0.0, le=1.0, description="Weighted combined score")


class JobSearchResponse(BaseModel):
    matches: list[JobMatchResult]
    total: int
    resume_id: str


class GapAnalysis(BaseModel):
    job_id: str
    job_title: str
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_nive_to_have_skills: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class JobRefreshRequest(BaseModel):
    query: str = Field(default="software engineer", description="Search query")
    location: str | None = Field(default=None, description="Location filter (Adzuna only)")
    limit: int = Field(default=50, ge=1, le=100, description="Max jobs per source")


class JobRefreshResponse(BaseModel):
    jobs_fetched: int
    jobs_saved: int
    duplicates_skipped: int
    sources: list[str]
    message: str


class ErrorResponse(BaseModel):
    detail: str
    error_type: str | None = None


class SkillGapDetail(BaseModel):
    skill: str
    category: str = Field(..., description="missing, weak, or strong")
    importance: str = Field(..., description="critical, important, or nice_to_have")
    recommendation: str


class GapAnalysisResponse(BaseModel):
    job_id: str
    job_title: str
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[SkillGapDetail] = Field(default_factory=list)
    overall_match_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    recommendations: list[str] = Field(default_factory=list)


class InterviewStartRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to interview for")


class QuestionDetail(BaseModel):
    text: str
    topic: str
    difficulty: str


class InterviewStartResponse(BaseModel):
    session_id: str
    job_id: str
    job_title: str
    first_question: QuestionDetail
    total_questions: int


class SubmitAnswerRequest(BaseModel):
    answer_text: str = Field(..., min_length=10, description="Answer to current question")


class SubmitAnswerResponse(BaseModel):
    session_id: str
    question_number: int
    next_question: QuestionDetail | None
    is_completed: bool


class QuestionAndAnswer(BaseModel):
    question_number: int
    topic: int
    difficulty: str
    question: str
    answer: str
    score: int = Field(..., ge=0, le=10)
    feedback: str


class InterviewFeedbackResponse(BaseModel):
    session_id: str
    job_id: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    final_feedback: str
    questions_and_answers: list[QuestionAndAnswer]
    completed_at: datetime


class InterviewSessionResponse(BaseModel):
    session_id: str
    job_id: str
    status: str
    current_question_index: int
    total_questions: int
    is_completed: bool
