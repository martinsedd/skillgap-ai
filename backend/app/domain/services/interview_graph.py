from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.domain.ports.llm_port import LLMPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class InterviewState(TypedDict):
    """State schema for interview conversation."""

    job_id: str
    job_title: str
    job_description: str
    resume_text: str
    skill_gaps: list[str]  # Focus areas for questions

    questions: list[dict]  # [{text,topic,difficulty}]
    answers: list[dict]  # [{text,score,feedback}]
    current_question_index: int

    total_questions: int
    overall_score: float | None
    final_feedback: str | None

    status: str  # "in_progress", "completed", "error"


class InterviewGraph:
    """LangGraph-based interview state machine."""

    def __init__(self, llm_service: LLMPort, total_questions: int = 5):
        self.llm_service = llm_service
        self.total_questions = total_questions
        self.graph: CompiledStateGraph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(InterviewState)

        workflow.add_node("generate_question", self._generate_question_node)
        workflow.add_node("evaluate_answer", self._evaluate_answer_node)
        workflow.add_node("calculate_final_score", self._calculate_final_score_node)

        workflow.set_entry_point("generate_question")

        workflow.add_conditional_edges(
            "generate_question",
            self._should_continue_after_question,
            {"wait_for_answer": END, "complete": "calculate_final_score"},
        )

        workflow.add_conditional_edges(
            "evaluate_answer",
            self._should_continue_after_evaluation,
            {
                "next_question": "generate_question",
                "complete": "calculate_final_score",
            },
        )

        workflow.add_edge("calculate_final_score", END)

        return workflow.compile()

    def _generate_question_node(self, state: InterviewState) -> InterviewState:
        logger.info(
            "generating_interview_question",
            question_index=state["current_question_index"],
        )

        topic = self._get_next_topic(state)
        difficulty = self._determine_difficulty(state)

        previous_questions = [q["text"] for q in state["questions"]]

        try:
            question_text = self.llm_service.generate_interview_question(
                job_description=state["job_description"],
                topic=topic,
                difficulty=difficulty,
                previous_question=previous_questions,
            )

            state["questions"].append(
                {
                    "text": question_text,
                    "topic": topic,
                    "difficulty": difficulty,
                }
            )

            logger.info(
                "interview_question_generated",
                topic=topic,
                difficulty=difficulty,
            )
        except Exception as e:
            logger.error("question_generation_failed", error=str(e), exc_info=True)
            state["status"] = "error"

        return state

    def _evaluate_answer_node(self, state: InterviewState) -> InterviewState:
        logger.info("evaluating_interview_answer")

        current_idx = state["current_question_index"]
        question = state["questions"][current_idx]

        if len(state["answers"]) <= current_idx:
            logger.error("no_answer_provided", question_index=current_idx)
            state["status"] = "error"
            return state

        answer = state["answers"][current_idx]

        try:
            evaluation = self._evaluate_answer_with_llm(
                question_text=question["text"],
                answer_text=answer["text"],
                topic=question["topic"],
            )

            state["current_question_index"] += 1

            logger.info(
                "answer_evaluated",
                score=evaluation["score"],
                question_index=current_idx,
            )
        except Exception as e:
            logger.error("answer_evaluation_failed", error=str(e), exc_info=True)
            state["status"] = "error"

        return state

    def _calculate_final_score_node(self, state: InterviewState) -> InterviewState:
        logger.info("calculating_final_interview_score")

        scores = [answer.get("score", 0) for answer in state["answers"] if "score" in answer]

        if not scores:
            state["overall_score"] = 0.0
            state["final_feedback"] = "Interview incomplete - no answers evaluated."
            state["status"] = "error"
            return state

        overall_score = sum(scores) / len(scores) / 10.0  # INFO: Normalize to 0-1
        state["overall_score"] = overall_score

        feedback_parts = []
        feedback_parts.append(f"Overall Score: {overall_score:.1%}\n")

        for i, (question, answer) in enumerate(zip(state["questions"], state["answers"]), 1):
            feedback_parts.append(f"\nQuestion {i} ({question['topic']}):")
            feedback_parts.append(f"Score: {answer.get('score', 0)}/10")
            feedback_parts.append(f"Feedback: {answer.get('feedback', 'N/A')}")

        state["final_feedback"] = "\n".join(feedback_parts)
        state["status"] = "completed"

        logger.info("final_score_calculated", overall_score=overall_score)

        return state

    def _should_continue_after_question(self, state: InterviewState) -> str:
        # If we've generated all questions, we're don
        if len(state["questions"]) >= state["total_questions"]:
            return "complete"

        return "wait_for_answer"

    def _should_continue_after_evaluation(self, state: InterviewState) -> str:
        # If we've answered all questions, calculate final score
        if state["current_question_index"] >= state["total_questions"]:
            return "complete"

        return "next_question"

    def _get_next_topic(self, state: InterviewState) -> str:
        question_idx = len(state["questions"])

        if state["skill_gaps"] and question_idx < len(state["skill_gaps"]):
            return state["skill_gaps"][question_idx]
        elif state["skill_gaps"]:
            # Wrap around if we have more questions than gaps
            return state["skill_gaps"][question_idx % len(state["skill_gaps"])]
        else:
            return "general technical competency"

    def _determine_difficulty(self, state: InterviewState) -> str:
        question_idx = len(state["questions"])

        if question_idx < 2:
            return "easy"
        elif question_idx < 4:
            return "medium"
        else:
            return "hard"

    def _evaluate_answer_with_llm(self, question_text: str, answer_text: str, topic: str) -> dict:
        # TODO: Implement LLM-based evaluation
        # For now, return mock evaluation
        logger.warning("using_mock_evaluation", topic=topic)

        return {
            "score": 7,
            "feedback": "Good answer. Consider elaborating on implementation details.",
        }

    def create_initial_state(
        self,
        job_id: str,
        job_title: str,
        job_description: str,
        resume_text: str,
        skill_gaps: list[str],
    ) -> InterviewState:
        return InterviewState(
            job_id=job_id,
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text,
            skill_gaps=skill_gaps[:5],
            questions=[],
            answers=[],
            current_question_index=0,
            total_questions=self.total_questions,
            overall_score=None,
            final_feedback=None,
            status="in_progress",
        )
