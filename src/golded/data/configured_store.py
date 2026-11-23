"""Route configured areas to their message stores."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from golded_ftn import OutgoingMessage, ParsedMessage, ParserException

from golded.data.area import Area
from golded.data.area_config import ConfiguredArea, area_code_key, load_area_config
from golded.data.hudson_store import HudsonBase, HudsonMessageStore
from golded.data.jam_store import JamMessageStore
from golded.data.msg_store import MsgMessageStore
from golded.data.store import MessageStore, open_message_store

_AREA_KINDS = {"echo": "echomail", "net": "netmail"}


@dataclass(frozen=True)
class AreaRoute:
    area: Area
    store: MessageStore
    code: str


class ConfiguredMessageStore(MessageStore):
    def __init__(self, routes: dict[str, AreaRoute]) -> None:
        self._routes = routes

    def areas(self) -> tuple[Area, ...]:
        return tuple(route.area for route in self._routes.values())

    def read_status(self, area: str) -> str:
        route = self._routes[area]
        return route.store.read_status(route.code)

    def messages(self, area: str) -> tuple[ParsedMessage, ...]:
        route = self._routes[area]
        return route.store.messages(route.code)

    def message(self, area: str, msgno: int) -> ParsedMessage:
        route = self._routes[area]
        return route.store.message(route.code, msgno)

    def append(self, area: str, message: OutgoingMessage) -> int:
        route = self._routes[area]
        return route.store.append(route.code, message)

    def delete(self, area: str, msgno: int) -> None:
        route = self._routes[area]
        route.store.delete(route.code, msgno)


def open_configured_store(
    path: Path,
    *,
    entries: tuple[ConfiguredArea, ...] | None = None,
    readonly: bool = False,
) -> ConfiguredMessageStore:
    routes: dict[str, AreaRoute] = {}
    hudson_bases: dict[Path, HudsonBase] = {}
    stores: dict[Path, tuple[MessageStore, dict[str, Area]]] = {}
    for entry in load_area_config(path) if entries is None else entries:
        source = (
            f"{path}:{entry.line}"
            if entry.line is not None
            else f"{path}: areas[{entry.code!r}]"
        )
        format_name = entry.format.casefold()
        if format_name not in {"sqlite", "jam", "msg", "opus", "hudson"}:
            raise ValueError(
                f"{source}: unsupported message-base format {entry.format}"
            )
        kind = _AREA_KINDS.get(entry.kind.casefold())
        if kind is None:
            raise ValueError(f"{source}: unsupported area type {entry.kind}")

        database = (path.parent / entry.location).resolve()
        area = Area(entry.code, entry.description, kind)
        if format_name == "jam":
            try:
                jam = JamMessageStore(database, area, lenient=entry.lenient)
            except (OSError, ParserException, ValueError) as error:
                raise ValueError(
                    f"{source}: cannot open JAM base {database}: {error}"
                ) from error
            routes[entry.code] = AreaRoute(area, jam, entry.code)
            continue

        if format_name in {"msg", "opus"}:
            try:
                msg = MsgMessageStore(database, area, opus=format_name == "opus")
            except (OSError, ParserException, ValueError) as error:
                raise ValueError(
                    f"{source}: cannot open {entry.format} area {database}: {error}"
                ) from error
            routes[entry.code] = AreaRoute(area, msg, entry.code)
            continue

        if format_name == "hudson":
            if entry.board is None:
                raise ValueError(f"{source}: Hudson board is required")
            try:
                if database not in hudson_bases:
                    hudson_bases[database] = HudsonBase(database, readonly=readonly)
            except (OSError, ParserException, ValueError) as error:
                raise ValueError(
                    f"{source}: cannot open Hudson base {database}: {error}"
                ) from error
            hudson = HudsonMessageStore(hudson_bases[database], area, board=entry.board)
            routes[entry.code] = AreaRoute(area, hudson, entry.code)
            continue

        if database not in stores:
            try:
                store = open_message_store(database)
                stores[database] = (
                    store,
                    {area_code_key(a.code): a for a in store.areas()},
                )
            except (OSError, sqlite3.Error, ValueError) as error:
                raise ValueError(
                    f"{source}: cannot open database {database}: {error}"
                ) from error

        store, areas = stores[database]
        stored = areas.get(area_code_key(entry.code))
        if stored is None:
            raise ValueError(f"{source}: area {entry.code} not found in {database}")
        if stored.kind != kind:
            raise ValueError(
                f"{source}: area {entry.code} is {stored.kind} in {database}, "
                f"but configured as {entry.kind}"
            )
        routes[entry.code] = AreaRoute(area, store, stored.code)
    return ConfiguredMessageStore(routes)
