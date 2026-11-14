"""GoldED-style pagebar (scrollbar in the right border column)."""

from textual.containers import Vertical
from textual.widgets import DataTable, Static


def fit_list_end(
    table: DataTable,
    main: Vertical,
    end: Static,
    pad: Static,
) -> None:
    frame_height = main.size.height
    if frame_height <= 0:
        return

    needed = table.row_count + 1

    if needed < frame_height:
        table.styles.height = needed
        line_width = main.size.width
        if line_width < 1:
            line_width = 1
        end.update("─" * line_width)
        end.styles.display = "block"
        pad.styles.display = "block"
    else:
        table.styles.height = "1fr"
        end.update("")
        end.styles.display = "none"
        pad.styles.display = "none"


def paint_pagebar(
    pagebar: Static,
    total: int,
    window: int,
    position: int,
    border_color: str,
    thumb_color: str,
) -> None:
    height = pagebar.size.height
    if height < 1:
        pagebar.update("")
        return

    if window < 1:
        window = 1

    if position < 0:
        position = 0

    cells = []
    for index in range(height):
        cells.append("track")

    if height >= 2:
        cells[0] = "▲"
        cells[height - 1] = "▼"

    if total > window and height > 2:
        track = height - 2
        max_pos = total - window
        if max_pos < 1:
            max_pos = 1

        thumb_len = (window * track) // total
        if thumb_len < 1:
            thumb_len = 1
        if thumb_len > track:
            thumb_len = track

        max_thumb = track - thumb_len
        thumb_pos = (position * max_thumb) // max_pos
        if thumb_pos > max_thumb:
            thumb_pos = max_thumb

        for index in range(thumb_len):
            cells[1 + thumb_pos + index] = "█"
    elif height == 1:
        cells[0] = "█"

    lines = []
    for cell in cells:
        if cell == "█" or cell == "▲" or cell == "▼":
            lines.append(f"[{thumb_color} on {border_color}]{cell}[/]")
        else:
            lines.append(f"[{border_color} on {border_color}]█[/]")

    pagebar.update("\n".join(lines))
