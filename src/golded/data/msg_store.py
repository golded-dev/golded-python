"""One classic FTSC MSG area backed by a directory of numbered files."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Literal

from golded_ftn import OutgoingMessage, ParsedMessage
from golded_ftn_msg import MsgReader, MsgWriter

from golded.data.area import Area
from golded.data.store import MessageStore

_LOCAL = 0x0100


class MsgMessageStore(MessageStore):
    def __init__(self, path: Path, area: Area, *, opus: bool = False) -> None:
        self._path = path
        self._area = area
        self._header_format: Literal["ftsc", "opus"] = "opus" if opus else "ftsc"
        self._reader = MsgReader(self._header_format)
        self._writer = MsgWriter()
        for _ in self._read(area.code):
            pass

    def areas(self) -> tuple[Area, ...]:
        return (self._area,)

    def _require_area(self, area: str) -> None:
        if area != self._area.code:
            raise KeyError(area)

    def _read(self, area: str) -> Iterator[ParsedMessage]:
        self._require_area(area)
        yield from self._reader.read(self._path)

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        return tuple(self._read(area))

    def message(self, area: str, msgno: int) -> ParsedMessage:
        for message in self._read(area):
            if message.msgno == msgno:
                return message
        raise KeyError(msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        self._require_area(area)
        now = datetime.now().replace(microsecond=0)
        if self._header_format == "opus":
            now = now.replace(second=now.second - now.second % 2)
        outgoing = replace(
            message,
            attributes_raw=(message.attributes_raw or 0) | _LOCAL,
            posted_at=message.posted_at or now,
        )
        with self._writer.open(
            self._path, header_format=self._header_format
        ) as session:
            return session.append(outgoing).identity.msgno

    def delete(self, area: str, msgno: int) -> None:
        self._require_area(area)
        with self._writer.open(
            self._path, header_format=self._header_format
        ) as session:
            stored = session.read(msgno)
            session.delete(stored.identity, stored.revision)
