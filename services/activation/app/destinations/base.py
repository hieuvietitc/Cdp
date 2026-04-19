from abc import ABC, abstractmethod


class BaseDestination(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def send(self, profiles: list[dict]) -> tuple[int, list[str]]:
        """
        Send profiles to the destination.
        Returns (sent_count, list_of_error_messages).
        """
        ...

    @abstractmethod
    def test(self) -> bool:
        """Verify that the destination credentials work."""
        ...
