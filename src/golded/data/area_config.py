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
    line: int
    lenient: bool = False


def load_area_config(path: Path) -> tuple[ConfiguredArea, ...]:
    areas: list[ConfiguredArea] = []
    codes: set[str] = set()
    read_modes: dict[str, tuple[bool, int]] = {}
    for number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
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
        if not _GROUP.fullmatch(group):
            raise ValueError(f"{path}:{number}: invalid group {group}")
        code = match["code"]
        key = area_code_key(code)
        if key in codes:
            raise ValueError(f"{path}:{number}: duplicate area code {code}")
        codes.add(key)
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
