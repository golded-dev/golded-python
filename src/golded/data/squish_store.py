"""One message area backed by an existing Squish base."""

from collections import Counter
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from golded_ftn import (
    ControlLine,
    OutgoingMessage,
    ParsedMessage,
    ReaderIssue,
)
from golded_ftn_squish import (
    SquishReader,
    SquishReaderOptions,
    SquishWriter,
    SquishWriterOptions,
)

from golded.data.area import Area
from golded.data.store import MessageStore

_LOCAL = 0x0100


class SquishMessageStore(MessageStore):
    def __init__(
        self,
        path: Path,
        area: Area,
        *,
        allow_unlinked_append: bool,
        readonly: bool = False,
        archive: bool = False,
        display_msgid_conflict: bool = False,
    ) -> None:
        self._path = path
        self._area = area
        self._reader = SquishReader()
        self._archive_read = archive
        self.readonly = archive and not display_msgid_conflict
        self._display_msgid_conflict = display_msgid_conflict
        self._archive_issues: Counter[tuple[str, str]] = Counter()
        self._writer = SquishWriter()
        self._allow_unlinked_append = allow_unlinked_append
        self._write_options = SquishWriterOptions(
            allow_unlinked_append=allow_unlinked_append
            and not (readonly or self.readonly)
        )
        for _ in self._read(area.code):
            pass

    def read_status(self, area: str) -> str:
        self._require_area(area)
        if not self._archive_read:
            return ""
        actions = Counter[str]()
        for (action, _), count in self._archive_issues.items():
            actions[action] += count
        counts = ", ".join(
            f"{actions[action]} {action}"
            for action in ("recovered", "skipped", "stopped")
        )
        mode = "lenient" if self._display_msgid_conflict else "archive"
        status = f"Squish {mode}: {counts}"
        return f"Read-only · {status}" if self.readonly else status

    def startup_diagnostics(self, area: str) -> str:
        summary = super().startup_diagnostics(area)
        if self._archive_read:
            details = ", ".join(
                f"{action}/{code}={count}"
                for (action, code), count in sorted(self._archive_issues.items())
            )
            return f"{summary}; {details}" if details else summary
        mode = "allow_unlinked_append" if self._allow_unlinked_append else "strict"
        offsets = self._writer.unlinked_frame_offsets(self._path)
        return f"{summary}; Squish: {len(offsets)} unlinked frames; write_mode={mode}"

    def areas(self) -> tuple[Area, ...]:
        return (self._area,)

    def _require_area(self, area: str) -> None:
        if area != self._area.code:
            raise KeyError(area)

    def _read(self, area: str) -> Iterator[ParsedMessage]:
        self._require_area(area)
        if not self._archive_read:
            yield from self._reader.read(self._path)
            return
        issues: Counter[tuple[str, str]] = Counter()

        def report(issue: ReaderIssue) -> None:
            issues[issue.action, issue.code] += 1

        options = SquishReaderOptions(
            archive_mode=True,
            on_issue=report,
            display_msgid_conflict=self._display_msgid_conflict,
        )
        messages = self._reader.read(self._path, options)
        yield from messages
        self._archive_issues = issues

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        return tuple(self._read(area))

    def message(self, area: str, msgno: int) -> ParsedMessage:
        for message in self._read(area):
            if message.msgno == msgno:
                return message
        raise KeyError(msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        self._require_area(area)
        if self.readonly:
            raise PermissionError("Squish archive area is read-only")
        outgoing = replace(
            message, attributes_raw=(message.attributes_raw or 0) | _LOCAL
        )
        if outgoing.posted_at is None:
            outgoing = replace(
                outgoing,
                posted_at=datetime.now(UTC).replace(tzinfo=None),
                control_lines=(
                    *(
                        line
                        for line in outgoing.control_lines
                        if line.name.upper() != "TZUTC"
                    ),
                    ControlLine(name="TZUTC", value="0000", raw="\x01TZUTC: 0000"),
                ),
            )
        with self._writer.open(self._path, self._write_options) as session:
            return session.append(outgoing).identity.msgno

    def delete(self, area: str, msgno: int) -> None:
        self._require_area(area)
        if self.readonly:
            raise PermissionError("Squish archive area is read-only")
        with self._writer.open(self._path) as session:
            stored = session.read(msgno)
            session.delete(stored.identity, stored.revision)
