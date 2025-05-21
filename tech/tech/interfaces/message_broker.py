from abc import ABC, abstractmethod
from typing import Any, Callable


class MessageBroker(ABC):
    @abstractmethod
    def publish(self, queue: str, message: dict) -> None:
        pass

    @abstractmethod
    def consume(self, queue: str, callback: Callable[[dict], None]) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass