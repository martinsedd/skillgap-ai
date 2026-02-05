import uuid
from datetime import datetime, timezone

from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repositories import JobRepository, ResumeRepository
from app.domain.services.interview_graph import InterviewGraph
from app.domain.services.skill_extraction_service import SkillExtractionService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class InterviewSession:
    def __init__(
        self,
        id: str,
        user_id: str,
        job_id: str,
        state: dict,
        created_at: datetime,
        completed_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.job_id = job_id
        self.state = state
        self.created_at = created_at
        self.completed_at = completed_at

    @property
    def is_completed(self) -> bool:
        return self.state["status"] == "completed"

    @property
    def current_question(self) -> dict | None:
        questions = self.state.get("questions", [])
        idx = self.state.get("current_question_index", 0)

        if 0 <= idx < len(questions):
            return questions[idx]

        return None

    @property
    def overall_score(self) -> float | None:
        return self.state.get("overall_score")

    @property
    def final_feedback(self) -> str | None:
        return self.state.get("final_feedback")


class InterviewService:
    def __init__(
        self,
        llm_service: LLMPort,
        skill_extraction_service: SkillExtractionService,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
        total_questions: int = 5,
    ) -> None:
        self.llm_service = llm_service
        self.skill_extraction_service = skill_extraction_service
        self.job_repository = job_repository
        self.resume_repository = resume_repository
        self.total_questions = total_questions

        self.interview_graph = InterviewGraph(
            llm_service=llm_service,
            total_questions=total_questions,
        )

        # In-memory session storage (Phase 3 will persist to DB)
        self._sessions: dict[str, InterviewSession] = {}

    def start_interview(self, user_id: str, job_id: str) -> InterviewSession:
        logger.info("starting_interview", user_id=user_id, job_id=job_id)

        job = self.job_repository.find_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        resume = self.resume_repository.find_by_user_id(user_id)
        if not resume:
            raise ValueError(f"No resume found for user {user_id}")

        gap_analysis = self.skill_extraction_service.analyze_gap(resume, job)
        skill_gaps = [gap.skill for gap in gap_analysis.missing_skills[:5]]

        initial_state = self.interview_graph.create_initial_state(
            job_id=job_id,
            job_title=job.title,
            job_description=job.description,
            resume_text=resume.text,
            skill_gaps=skill_gaps,
        )

        result_state: dict = self.interview_graph.graph.invoke(initial_state)

        session = InterviewSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            job_id=job_id,
            state=result_state,
            created_at=datetime.now(timezone.utc),
        )

        self._sessions[session.id] = session

        logger.info(
            "interview_started",
            session_id=session.id,
            first_question=(
                session.current_question.get("text") if session.current_question else None
            ),
        )

        return session

    def submit_answer(self, session_id: str, answer_text: str) -> InterviewSession:
        logger.info("submitting_interview_answer", session_id=session_id)

        session = self.get_session(session_id)

        if session.is_completed:
            raise ValueError("Interview already completed")

        session.state["answers"].append({"text": answer_text})

        result_state = self.interview_graph.graph.invoke(session.state)

        session.state = result_state

        if session.is_completed:
            session.completed_at = datetime.now(timezone.utc)
            logger.info(
                "interview_completed",
                session_id=session_id,
                overall_score=session.overall_score,
            )
        else:
            logger.info(
                "answer_submitted",
                session_id=session_id,
                next_question=(
                    session.current_question.get("text") if session.current_question else None
                ),
            )

        return session

    def get_session(self, session_id: str) -> InterviewSession:
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session {session_id} not found")
        return session

    def get_feedback(self, session_id: str) -> dict:
        logger.info("getting_interview_feedback", session_id=session_id)

        session = self.get_session(session_id)

        if not session.is_completed:
            raise ValueError("Interview not completed yet")

        questions_and_answers = []
        for i, (question, answer) in enumerate(
            zip(session.state["questions"], session.state["answers"]),
        ):
            questions_and_answers.append(
                {
                    "question_number": i,
                    "topic": question.get("topic"),
                    "difficulty": question.get("difficulty"),
                    "question": question.get("text"),
                    "answer": answer.get("text"),
                    "score": answer.get("score"),
                    "feedback": answer.get("feedback"),
                }
            )

        return {
            "session_id": session.id,
            "job_id": session.job_id,
            "overall_score": session.overall_score,
            "final_feedback": session.final_feedback,
            "questions_and_answers": questions_and_answers,
            "completed_at": session.completed_at,
        }
