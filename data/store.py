"""Message store ABC and open/create entry points; implementation in sqlite_store."""

from abc import ABC, abstractmethod

from golded_ftn import OutgoingMessage, ParsedMessage

from data.area import Area

class MessageStore(ABC):
    @abstractmethod
    def areas(self) -> tuple[Area, ...]:
        pass

    @abstractmethod
    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        pass

    @abstractmethod
    def message(self, area: str, msgno: int) -> ParsedMessage:
        pass

    @abstractmethod
    def append(self, area: str, message: OutgoingMessage) -> int:
        pass

    @abstractmethod
    def delete(self, area: str, msgno: int) -> None:
        pass

def open_message_store(path: str) -> MessageStore:
    from data.sqlite_store import open_message_store as open_store

    return open_store(path)

def create_message_store(
    path: str,
    areas: list[Area],
    default_origin: str | None = None,
) -> MessageStore:
    from data.sqlite_store import create_message_store as create_store

    return create_store(path, areas, default_origin)
