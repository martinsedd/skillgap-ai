from abc import ABC, abstractmethod


class AuthPort(ABC):
    """Port for authentication."""

    @abstractmethod
    def validate_token(self, token: str) -> str | None:
        ...

    @abstractmethod
    def get_current_user_id(self, token: str) -> str:
        ...
