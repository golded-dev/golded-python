"""GoldED colour themes (IBM VGA names, hex as in DOS text mode)."""

from textual.theme import Theme

BLACK = "#000000"
BLUE = "#0000aa"
RED = "#aa0000"
LGREY = "#aaaaaa"
LGREY_LIGHT = "#cccccc"
DGREY = "#555555"
YELLOW = "#ffff55"
WHITE = "#ffffff"
LOGO_YELLOW = "#ffe45a"

DARK = Theme(
    name="dark",
    primary=BLUE,
    foreground=LGREY,
    background=BLACK,
    surface=BLACK,
    panel=BLACK,
    dark=True,
    variables={
        "ged-bg": BLACK,
        "ged-fg": LGREY,
        "ged-line": BLUE,
        "ged-title": YELLOW,
        "ged-border": BLUE,
        "ged-msg-border": RED,
        "ged-subtitle": YELLOW,
        "ged-status-bg": BLUE,
        "ged-status-fg": WHITE,
        "ged-cursor-bg": BLUE,
        "ged-cursor-fg": WHITE,
        "ged-header": YELLOW,
        "ged-meta": LGREY,
        "ged-body": LGREY,
        "ged-tag": WHITE,
        "ged-prompt": WHITE,
        "ged-logo": LOGO_YELLOW,
        "ged-endline": LGREY,
        "ged-scroll": BLUE,
    },
)

# Light theme from classic GoldED Black on LGrey (gedcol22/23).
LIGHT = Theme(
    name="light",
    primary=BLUE,
    foreground=BLACK,
    background=LGREY_LIGHT,
    surface=LGREY_LIGHT,
    panel=LGREY_LIGHT,
    dark=False,
    variables={
        "ged-bg": LGREY_LIGHT,
        "ged-fg": BLACK,
        "ged-line": YELLOW,
        "ged-title": RED,
        "ged-border": BLUE,
        "ged-msg-border": RED,
        "ged-subtitle": RED,
        "ged-status-bg": BLUE,
        "ged-status-fg": WHITE,
        "ged-cursor-bg": BLUE,
        "ged-cursor-fg": WHITE,
        "ged-header": RED,
        "ged-meta": BLUE,
        "ged-body": BLACK,
        "ged-tag": BLACK,
        "ged-prompt": BLACK,
        "ged-logo": BLUE,
        "ged-endline": DGREY,
        "ged-scroll": DGREY,
    },
)

THEMES = (DARK, LIGHT)
DEFAULT_THEME = DARK.name
