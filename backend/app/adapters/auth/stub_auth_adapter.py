from app.core.config import settings
from app.domain.ports.auth_port import AuthPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class StubAuthAdapter(AuthPort):
    """
    Stub authentication adapter for development.
    Always returns configured stub user ID.
    """

    def __init__(self, stub_user_id: str):
        self.stub_user_id = stub_user_id
        logger.info("stub_auth_initialized", user_id=stub_user_id)

    def validate_token(self, token: str) -> str | None:
        """
        Validate token (stub: accepts any non-empty token).
        Returns stub user ID if token is valid, None otherwise.
        """
        if not token or token.strip() == "":
            logger.warning("invalid_token", reason="empty_or_none")
            return None

        logger.debug("token_validated", user_id=self.stub_user_id)
        return self.stub_user_id

    def get_current_user_id(self, token: str) -> str:
        """
        Get current user ID from token.
        Raises ValueError if token is invalid.
        """
        user_id = self.validate_token(token)

        if not user_id:
            logger.error("authentication_failed", token_length=len(token) if token else 0)
            raise ValueError("Invalid authentication token")

        return user_id


def create_stub_auth_adapter() -> StubAuthAdapter:
    return StubAuthAdapter(stub_user_id=settings.AUTH_STUB_USER_ID)
