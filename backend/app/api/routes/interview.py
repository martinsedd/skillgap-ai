from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_interview_service
from app.api.schemas import (
    InterviewFeedbackResponse,
    InterviewSessionResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    QuestionAndAnswer,
    QuestionDetail,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.domain.services.interview_service import InterviewService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    request: InterviewStartRequest,
    user_id: str = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    logger.info("interview_start_request", user_id=user_id, job_id=request.job_id)

    try:
        session = interview_service.start_interview(user_id, request.job_id)

        first_question = session.current_question
        if not first_question:
            raise HTTPException(status_code=500, detail="Failed to generate first question")

        return InterviewStartResponse(
            session_id=session.id,
            job_id=session.job_id,
            job_title=session.state["job_title"],
            first_question=QuestionDetail(
                text=first_question["text"],
                topic=first_question["topic"],
                difficulty=first_question["difficulty"],
            ),
            total_questions=session.state["total_questions"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("interview_start_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    user_id: str = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    logger.info("submit_answer_request", session_id=session_id, user_id=user_id)

    try:
        session = interview_service.submit_answer(session_id, request.answer_text)

        next_question = session.current_question
        question_number = len(session.state["answers"])

        return SubmitAnswerResponse(
            session_id=session.id,
            question_number=question_number,
            next_question=(
                QuestionDetail(
                    text=next_question["text"],
                    topic=next_question["topic"],
                    difficulty=next_question["difficulty"],
                )
                if next_question
                else None
            ),
            is_completed=session.is_completed,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("submit_answer_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.get("/{session_id}/feedback", response_model=InterviewFeedbackResponse)
async def get_feedback(
    session_id: str,
    user_id: str = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    logger.info("feedback_request", session_id=session_id, user_id=user_id)

    try:
        feedback = interview_service.get_feedback(session_id)

        return InterviewFeedbackResponse(
            session_id=feedback["session_id"],
            job_id=feedback["job_id"],
            overall_score=feedback["overall_score"],
            final_feedback=feedback["final_feedback"],
            questions_and_answers=[
                QuestionAndAnswer(**qa) for qa in feedback["questions_and_answers"]
            ],
            completed_at=feedback["completed_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("feedback_request_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
    interview_service: InterviewService = Depends(get_interview_service),
):
    logger.info("session_request", session_id=session_id, user_id=user_id)

    try:
        session = interview_service.get_session(session_id)

        return InterviewSessionResponse(
            session_id=session.id,
            job_id=session.job_id,
            status=session.state["status"],
            current_question_index=session.state["current_question_index"],
            total_questions=session.state["total_questions"],
            is_completed=session.is_completed,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("session_request_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")
