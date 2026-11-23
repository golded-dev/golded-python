"""One configured board in a shared Hudson message base."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from golded_ftn import OutgoingMessage, ParsedMessage
from golded_ftn_hudson import HudsonReader, HudsonWriter

from golded.data.area import Area
from golded.data.store import MessageStore

_LOCAL = 0x40
_NETMAIL = 0x04


class HudsonBase:
    def __init__(self, path: Path, *, readonly: bool) -> None:
        self.path = path
        self._reader = HudsonReader()
        self._snapshot: dict[str | None, list[ParsedMessage]] | None = (
            {} if readonly else None
        )
        for message in self._reader.read(path):
            if self._snapshot is not None:
                self._snapshot.setdefault(message.area, []).append(message)

    def read_board(self, board_code: str) -> Iterator[ParsedMessage]:
        if self._snapshot is not None:
            yield from self._snapshot.get(board_code, ())
            return
        for message in self._reader.read(self.path):
            if message.area == board_code:
                yield message


class HudsonMessageStore(MessageStore):
    def __init__(self, base: HudsonBase, area: Area, *, board: int) -> None:
        self._base = base
        self._area = area
        self._board = board
        self._board_code = f"BOARD{board}"
        self._writer = HudsonWriter()

    def areas(self) -> tuple[Area, ...]:
        return (self._area,)

    def _require_area(self, area: str) -> None:
        if area != self._area.code:
            raise KeyError(area)

    def _read(self, area: str) -> Iterator[ParsedMessage]:
        self._require_area(area)
        yield from self._base.read_board(self._board_code)

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        return tuple(self._read(area))

    def message(self, area: str, msgno: int) -> ParsedMessage:
        for message in self._read(area):
            if message.msgno == msgno:
                return message
        raise KeyError(msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        self._require_area(area)
        flags = _LOCAL | (_NETMAIL if self._area.kind == "netmail" else 0)
        outgoing = replace(
            message,
            attributes_raw=(message.attributes_raw or 0) | flags,
            posted_at=message.posted_at or datetime.now(),
        )
        with self._writer.open(self._base.path, board=self._board) as session:
            return session.append(outgoing).identity.msgno

    def delete(self, area: str, msgno: int) -> None:
        self._require_area(area)
        with self._writer.open(self._base.path, board=self._board) as session:
            stored = session.read(msgno)
            session.delete(stored.identity, stored.revision)
