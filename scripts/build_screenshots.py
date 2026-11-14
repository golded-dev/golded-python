"""Render the manual's screenshots as SVG from the demo database.

The clock is frozen and the database is the seeded demo, so a rerun gives the
same files unless the UI changed. Textual's SVG export loads Fira Code from a
CDN; the font rules are removed and the text uses the manual's IBM Plex Mono,
so the pages stay free of network requests.
"""

import asyncio
import re
import tempfile
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Self
from unittest import mock

from textual.pilot import Pilot

from golded.data.store import open_message_store
from golded.logic.session import Session
from golded.ui.app import GoldED
from seed_demo import seed_database

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "screens"
SIZE = (80, 25)
THEMES = ("dark", "light")


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: object = None) -> Self:
        return cls(2026, 11, 14, 9, 41, 0)


async def splash(pilot: Pilot[None]) -> None:
    await pilot.pause()


async def area_list(pilot: Pilot[None]) -> None:
    await pilot.press("space")


async def message_list(pilot: Pilot[None]) -> None:
    await pilot.press("space", "t", "h", "r", "enter")
    await pilot.pause()
    await pilot.press("t")


async def message_view(pilot: Pilot[None]) -> None:
    await message_list(pilot)
    await pilot.pause()
    await pilot.press("enter")


async def reply(pilot: Pilot[None]) -> None:
    await message_view(pilot)
    await pilot.pause()
    await pilot.press("r")


SCREENS: tuple[tuple[str, Callable[[Pilot[None]], Awaitable[None]]], ...] = (
    ("splash", splash),
    ("area-list", area_list),
    ("message-list", message_list),
    ("message-view", message_view),
    ("reply", reply),
)


def local_fonts(svg: str) -> str:
    svg = re.sub(r"\s*@font-face \{.*?\}", "", svg, flags=re.DOTALL)
    svg = svg.replace(
        "font-family: Fira Code, monospace", "font-family: 'IBM Plex Mono', monospace"
    )
    svg = svg.replace("font-family: arial", "font-family: 'IBM Plex Sans', sans-serif")
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", "").replace(
        "https://www.textualize.io", ""
    ), "unexpected remote reference in SVG"
    return svg


async def capture(
    database: Path, theme: str, steps: Callable[[Pilot[None]], Awaitable[None]]
) -> str:
    app = GoldED(Session(open_message_store(database)), theme)
    async with app.run_test(size=SIZE) as pilot:
        await steps(pilot)
        await pilot.pause()
        return app.export_screenshot(title="golded")


async def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryDirectory() as temporary,
        mock.patch("golded.ui.status.datetime", FrozenDateTime),
        mock.patch("golded.ui.write_message.datetime", FrozenDateTime),
    ):
        for theme in THEMES:
            for name, steps in SCREENS:
                # A fresh demo base per shot, so no screen sees another's writes.
                database = seed_database(Path(temporary) / f"{theme}-{name}.sqlite3")
                svg = local_fonts(await capture(database, theme, steps))
                (OUTPUT / f"{name}-{theme}.svg").write_text(svg, encoding="utf-8")
    print(
        f"Wrote {len(THEMES) * len(SCREENS)} screenshots to {OUTPUT.relative_to(ROOT)}."
    )


if __name__ == "__main__":
    asyncio.run(main())
