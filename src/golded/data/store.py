"""Message store ABC and open/create entry points."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from golded_ftn import FtnAddress, OutgoingMessage, ParsedMessage

from golded.data.area import Area
from golded.data.area_config import ConfiguredArea


class MessageStore(ABC):
    readonly = False

    def area_readonly(self, area: str) -> bool:
        return self.readonly

    def read_status(self, area: str) -> str:
        return ""

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


class ReadOnlyMessageStore(MessageStore):
    readonly = True

    def __init__(self, store: MessageStore) -> None:
        self._store = store

    def areas(self) -> tuple[Area, ...]:
        return self._store.areas()

    def read_status(self, area: str) -> str:
        status = self._store.read_status(area)
        if self._store.area_readonly(area):
            return status
        return f"Read-only · {status}" if status else "Read-only"

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        return self._store.messages(area)

    def message(self, area: str, msgno: int) -> ParsedMessage:
        for message in self.messages(area):
            if message.msgno == msgno:
                return message
        raise KeyError(msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        raise PermissionError("Message store is read-only")

    def delete(self, area: str, msgno: int) -> None:
        raise PermissionError("Message store is read-only")


def open_message_store(path: str | Path, *, readonly: bool = False) -> MessageStore:
    from golded.data.sqlite_store import open_message_store as open_store

    store = open_store(path)
    return ReadOnlyMessageStore(store) if readonly else store


def open_configured_store(
    path: str | Path,
    *,
    entries: tuple[ConfiguredArea, ...] | None = None,
    readonly: bool = False,
) -> MessageStore:
    from golded.data.configured_store import open_configured_store as open_store

    store = open_store(Path(path), entries=entries)
    return ReadOnlyMessageStore(store) if readonly else store


def create_message_store(
    path: str | Path,
    areas: Sequence[Area],
    default_origin: FtnAddress | None = None,
) -> MessageStore:
    from golded.data.sqlite_store import create_message_store as create_store

    return create_store(path, areas, default_origin)
