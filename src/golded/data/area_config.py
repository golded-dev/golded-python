"""Read the AREADEF subset of classic GoldED configuration."""

import re
from dataclasses import dataclass, replace
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase

_AREADEF = re.compile(
    r'AREADEF\s+(?P<code>[^\s";]+)\s+"(?P<description>[^"]*)"\s+'
    r'(?P<group>[^\s";]+)\s+(?P<kind>[^\s";]+)\s+(?P<format>[^\s";]+)\s+'
    r'(?:"(?P<quoted_location>[^"]+)"|(?P<location>[^\s";]+))'
    r'(?:\s+[^\s;"()]+\s+\([^);]*\)(?:\s+"[^"]*")?)?'
    r"\s*(?:;.*)?",
    re.IGNORECASE,
)
_HUDSONPATH = re.compile(
    r'HUDSONPATH\s+(?:"([^"]+)"|([^\s";]+))\s*(?:;.*)?', re.IGNORECASE
)
_JAMREAD = re.compile(
    r"JAMREAD\s+(?:([^\s;]+)\s+)?(strict|lenient)\s*(?:;.*)?", re.IGNORECASE
)
_GROUP = re.compile(r"[A-Z]|0|#[1-9][0-9]{0,2}", re.IGNORECASE | re.ASCII)
_ASCII_LOWER = str.maketrans(ascii_uppercase, ascii_lowercase)


def area_code_key(code: str) -> str:
    # Match SQLite's NOCASE collation without merging distinct non-ASCII codes.
    return code.translate(_ASCII_LOWER)


@dataclass(frozen=True)
class ConfiguredArea:
    code: str
    description: str
    group: str
    kind: str
    format: str
    location: str
    line: int | None = None
    lenient: bool = False
    board: int | None = None


def load_area_config(path: Path) -> tuple[ConfiguredArea, ...]:
    areas: list[ConfiguredArea] = []
    codes: set[str] = set()
    read_modes: dict[str, tuple[bool, int]] = {}
    hudson_path: str | None = None
    for number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if re.match(r"HUDSONPATH(?=\s|;|$)", line, re.IGNORECASE):
            path_match = _HUDSONPATH.fullmatch(line)
            if path_match is None or hudson_path is not None:
                raise ValueError(f"{path}:{number}: expected a single HUDSONPATH")
            hudson_path = path_match[1] or path_match[2]
            continue
        if re.match(r"JAMREAD(?=\s|;|$)", line, re.IGNORECASE):
            directive = _JAMREAD.fullmatch(line)
            if directive is None:
                raise ValueError(
                    f"{path}:{number}: expected JAMREAD [area] strict|lenient"
                )
            target, mode = directive.groups()
            key = area_code_key(target) if target is not None else ""
            if key in read_modes:
                scope = target if target is not None else "global default"
                raise ValueError(f"{path}:{number}: duplicate JAMREAD for {scope}")
            read_modes[key] = (mode.lower() == "lenient", number)
            continue
        if not re.match(r"AREADEF(?=\s|;|$)", line, re.IGNORECASE):
            continue
        match = _AREADEF.fullmatch(line)
        if match is None:
            raise ValueError(f"{path}:{number}: malformed AREADEF")
        group = match["group"]
        code = match["code"]
        validate_area_identity(code, group, codes, f"{path}:{number}")
        areas.append(
            ConfiguredArea(
                code=code,
                description=match["description"],
                group=group,
                kind=match["kind"],
                format=match["format"],
                location=match["quoted_location"] or match["location"],
                line=number,
            )
        )
    for index, area in enumerate(areas):
        if area.format.casefold() != "hudson":
            continue
        source = f"{path}:{area.line}"
        if hudson_path is None:
            raise ValueError(f"{source}: Hudson areas require HUDSONPATH")
        board = (
            int(area.location) if re.fullmatch(r"[0-9]{1,3}", area.location) else None
        )
        areas[index] = replace(
            area, location=hudson_path, board=_hudson_board(board, source)
        )
    if not areas:
        raise ValueError(f"{path}: no AREADEF entries")
    jam_codes = {
        area_code_key(area.code) for area in areas if area.format.lower() == "jam"
    }
    for target, (_, number) in read_modes.items():
        if target and target not in jam_codes:
            raise ValueError(
                f"{path}:{number}: JAMREAD target {target} is not a configured JAM area"
            )
    default, _ = read_modes.get("", (False, 0))
    return tuple(
        replace(area, lenient=read_modes.get(area_code_key(area.code), (default, 0))[0])
        if area.format.lower() == "jam"
        else area
        for area in areas
    )


def validate_area_identity(code: str, group: str, codes: set[str], source: str) -> None:
    if not re.fullmatch(r'[^\s";]+', code):
        raise ValueError(f"{source}: invalid area code {code!r}")
    if not _GROUP.fullmatch(group):
        raise ValueError(f"{source}: invalid group {group}")
    key = area_code_key(code)
    if key in codes:
        raise ValueError(f"{source}: duplicate area code {code}")
    codes.add(key)


def parse_toml_areas(areas: object, jam: object) -> tuple[ConfiguredArea, ...]:
    if not isinstance(jam, dict):
        raise ValueError("jam must be a table")
    if not isinstance(areas, dict):
        raise ValueError("areas must be a table")
    default = _toml_read_mode(jam.get("read_mode", "strict"), "jam.read_mode")
    codes: set[str] = set()
    entries: list[ConfiguredArea] = []
    for code, fields in areas.items():
        source = f"areas[{code!r}]"
        if not isinstance(fields, dict):
            raise ValueError(f"{source} must be a table")
        description, group, kind, format_name, location = (
            _toml_area_field(fields, field, source)
            for field in ("description", "group", "type", "format", "path")
        )
        validate_area_identity(code, group, codes, source)
        is_jam = format_name.casefold() == "jam"
        lenient = is_jam and default
        if "read_mode" in fields:
            if not is_jam:
                raise ValueError(f"{source}.read_mode is only valid for JAM areas")
            lenient = _toml_read_mode(fields["read_mode"], f"{source}.read_mode")
        if format_name.casefold() == "hudson":
            board = _hudson_board(fields.get("board"), source)
        elif "board" in fields:
            raise ValueError(f"{source}.board is only valid for Hudson areas")
        else:
            board = None
        entries.append(
            ConfiguredArea(
                code,
                description,
                group,
                kind,
                format_name,
                location,
                lenient=lenient,
                board=board,
            )
        )
    return tuple(entries)


def _hudson_board(value: object, source: str) -> int:
    if type(value) is not int or not 1 <= value <= 200:
        raise ValueError(f"{source}: Hudson board must be an integer from 1 to 200")
    return value


def _toml_area_field(fields: dict[str, object], field: str, source: str) -> str:
    value = fields.get(field)
    if not isinstance(value, str) or (field != "description" and not value.strip()):
        raise ValueError(f"{source}.{field} must be a string with a value")
    return value


def _toml_read_mode(value: object, source: str) -> bool:
    if not isinstance(value, str) or value.lower() not in {"strict", "lenient"}:
        raise ValueError(f"{source} must be strict or lenient, got {value!r}")
    return value.lower() == "lenient"
