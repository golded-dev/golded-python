"""GoldED-style area title bar."""

def area_title_line(
    area_name: str,
    area_code: str,
    width: int,
    line_color: str,
    title_color: str,
) -> str:
    if width < 40:
        width = 80

    title_left = f" {area_name} "
    title_right = f" {area_code} "
    fill = width - 2 - len(title_left) - len(title_right)
    if fill < 1:
        fill = 1

    return (
        f"[{line_color}]─[/]"
        f"[{title_color}]{title_left}[/]"
        f"[{line_color}]{'─' * fill}[/]"
        f"[{title_color}]{title_right}[/]"
        f"[{line_color}]─[/]"
    )
