"""One JAM message area backed by an existing set of JAM files."""

from collections import Counter
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from golded_ftn import OutgoingMessage, ParsedMessage, ReaderIssue, ReaderOptions
from golded_ftn_jam import JamReader, JamWriter

from golded.data.area import Area
from golded.data.store import MessageStore

# JAM revision 1 attribute bits for a locally composed message.
_LOCAL = 0x00000001
_TYPE_ECHO = 0x01000000
_TYPE_NET = 0x02000000


class JamMessageStore(MessageStore):
    def __init__(self, path: Path, area: Area, *, lenient: bool) -> None:
        self._path = path
        self._area = area
        self._reader = JamReader()
        self._writer = JamWriter()
        self._lenient = lenient
        self._issues: Counter[str] = Counter()
        # Validate the existing base before handing it to the UI.
        for _ in self._read():
            pass

    def areas(self) -> tuple[Area, ...]:
        return (self._area,)

    def read_status(self, area: str) -> str:
        if area != self._area.code:
            raise KeyError(area)
        if not self._lenient:
            return ""
        counts = ", ".join(
            f"{self._issues[action]} {action}"
            for action in ("recovered", "skipped", "stopped")
        )
        return f"JAM lenient: {counts}"

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        if area != self._area.code:
            raise KeyError(area)
        return tuple(self._read())

    def _read(self) -> Iterator[ParsedMessage]:
        if not self._lenient:
            yield from self._reader.read(self._path)
            return

        issues: Counter[str] = Counter()

        def report(issue: ReaderIssue) -> None:
            issues[issue.action] += 1

        options = ReaderOptions(archive_mode=True, on_issue=report)
        yield from self._reader.read(self._path, options)
        self._issues = issues

    def message(self, area: str, msgno: int) -> ParsedMessage:
        if area != self._area.code:
            raise KeyError(area)
        for message in self._read():
            if message.msgno == msgno:
                return message
        raise KeyError(msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        if area != self._area.code:
            raise KeyError(area)
        flags = _TYPE_NET if self._area.kind == "netmail" else _TYPE_ECHO
        outgoing = replace(
            message,
            attributes_raw=(message.attributes_raw or 0) | _LOCAL | flags,
            # Without a TZUTC control, JamWriter interprets a naive time as UTC.
            posted_at=message.posted_at or datetime.now(UTC).replace(tzinfo=None),
        )
        with self._writer.open(self._path) as session:
            return session.append(outgoing).identity.msgno

    def delete(self, area: str, msgno: int) -> None:
        if area != self._area.code:
            raise KeyError(area)
        with self._writer.open(self._path) as session:
            stored = session.read(msgno)
            session.delete(stored.identity, stored.revision)
