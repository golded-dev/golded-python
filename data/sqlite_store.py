"""SQLite message store."""

from pathlib import Path

from golded_ftn import OutgoingMessage, ParsedMessage
from golded_ftn_sqlite import (
    AreaDefinition,
    AreaKind,
    SqliteDatabase,
    SqliteReader,
    SqliteWriter,
)

from data.area import Area
from data.store import MessageStore

def _to_definition(area: Area, default_origin: str | None = None) -> AreaDefinition:
    return AreaDefinition(
        code = area.code,
        name = area.name,
        kind = AreaKind(area.kind),
        default_origin = default_origin,
    )

def _from_definition(area: AreaDefinition) -> Area:
    if area.kind is AreaKind.NETMAIL:
        kind = "netmail"
    else:
        kind = "echomail"

    return Area(area.code, area.name, kind)

class SqliteMessageStore(MessageStore):
    def __init__(self, path: Path) -> None:
        self.__path = path
        self.__db = SqliteDatabase.open(path)

    def areas(self) -> tuple[Area, ...]:
        result = []
        for area in self.__db.areas():
            result.append(_from_definition(area))

        return tuple(result)

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        result = []
        for message in SqliteReader(area).read(self.__path):
            result.append(message)

        return tuple(result)

    def message(self, area: str, msgno: int) -> ParsedMessage:
        with SqliteWriter(area).open(self.__path) as session:
            return session.read(msgno).message

    def append(self, area: str, message: OutgoingMessage) -> int:
        with SqliteWriter(area).open(self.__path) as session:
            result = session.append(message)

        return result.identity.msgno

    def delete(self, area: str, msgno: int) -> None:
        with SqliteWriter(area).open(self.__path) as session:
            stored = session.read(msgno)
            session.delete(stored.identity, stored.revision)

def open_message_store(path) -> SqliteMessageStore:
    return SqliteMessageStore(Path(path).resolve())

def create_message_store(path, areas, default_origin = None) -> SqliteMessageStore:
    if len(areas) == 0:
        raise ValueError("at least one area is required")

    database_path = Path(path).resolve()

    first = areas[0]

    SqliteDatabase.create(
        database_path,
        area = _to_definition(first, default_origin),
    )

    db = SqliteDatabase.open(database_path)
    for area in areas[1:]:
        db.add_area(_to_definition(area))

    return SqliteMessageStore(database_path)
