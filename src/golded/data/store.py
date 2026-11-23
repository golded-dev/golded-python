"""Message store ABC and open/create entry points."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from golded_ftn import FtnAddress, OutgoingMessage, ParsedMessage

from golded.data.area import Area


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


def open_message_store(path: str | Path) -> MessageStore:
    from golded.data.sqlite_store import open_message_store as open_store

    return open_store(path)


def open_configured_store(path: str | Path) -> MessageStore:
    from golded.data.configured_store import open_configured_store as open_store

    return open_store(Path(path))


def create_message_store(
    path: str | Path,
    areas: Sequence[Area],
    default_origin: FtnAddress | None = None,
) -> MessageStore:
    from golded.data.sqlite_store import create_message_store as create_store

    return create_store(path, areas, default_origin)
