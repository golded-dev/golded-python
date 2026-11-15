"""GoldED-style area title bar."""

from rich.text import Text


def area_title_line(
    area_name: str,
    area_code: str,
    width: int,
    line_color: str,
    title_color: str,
) -> Text:
    if width < 40:
        width = 80

    title_left = f" {area_name} "
    title_right = f" {area_code} "
    fill = width - 2 - len(title_left) - len(title_right)
    if fill < 1:
        fill = 1

    # Text, not markup: area names come from the base and may contain [brackets].
    return Text.assemble(
        ("─", line_color),
        (title_left, title_color),
        ("─" * fill, line_color),
        (title_right, title_color),
        ("─", line_color),
    )
