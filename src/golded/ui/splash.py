"""Brag splash screen (classic GoldED copyright window)."""

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from golded.logic.version import (
    AUTHOR,
    COPYRIGHT_YEARS,
    PRODUCT,
    PRODUCT_DESCRIPTION,
    RELEASE_NAME,
)
from golded.ui.logo import LOGO

COUNTDOWN_SECONDS = 10

CREDITS = (
    f"{PRODUCT_DESCRIPTION}\n"
    f"By {AUTHOR}\n"
    "\n"
    f"{PRODUCT}\n"
    "\n"
    f"Copyright (C) {COPYRIGHT_YEARS}"
)

LICENSE_TEXT = (
    "This program is free software; it is licensed under the\n"
    "MIT License. You're welcome to use, copy, modify and\n"
    "distribute it. See LICENSE for the full terms."
)


class SplashScreen(Screen):
    DEFAULT_CSS = """
    SplashScreen {
        align: center middle;
    }

    SplashScreen #brag {
        width: 100%;
        height: 100%;
        border: solid $ged-border;
        background: $ged-bg;
        color: $ged-fg;
        padding: 0 1;
    }

    SplashScreen #brag-top {
        height: auto;
        margin-top: 1;
    }

    SplashScreen #logo {
        width: 45;
        height: auto;
        color: $ged-logo;
    }

    SplashScreen #credits {
        width: 1fr;
        height: auto;
        color: $ged-fg;
        content-align: center middle;
        padding-left: 2;
    }

    SplashScreen #release {
        width: 100%;
        height: auto;
        content-align: center middle;
        color: $ged-title;
        margin-top: 4;
    }

    SplashScreen #mid {
        width: 100%;
        height: 1fr;
        align: center middle;
    }

    SplashScreen #license {
        width: 100%;
        height: auto;
        content-align: center middle;
        color: $ged-fg;
    }

    SplashScreen #prompt {
        width: 100%;
        height: auto;
        content-align: center middle;
        color: $ged-prompt;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.__left = COUNTDOWN_SECONDS
        self.__done = False

    def compose(self) -> ComposeResult:
        with Vertical(id="brag"):
            with Horizontal(id="brag-top"):
                yield Static(LOGO, id="logo")
                yield Static(CREDITS, id="credits")
            yield Static(
                f"---*-*-*** {RELEASE_NAME} ***-*-*---",
                id="release",
            )
            with Vertical(id="mid"):
                yield Static(LICENSE_TEXT, id="license")
            yield Static(self.prompt_text(), id="prompt")

    def prompt_text(self) -> str:
        return f"Press any key or wait  {self.__left}"

    def on_mount(self) -> None:
        self.set_timer(1.0, self.tick_countdown)

    def tick_countdown(self) -> None:
        if self.__done:
            return

        self.__left = self.__left - 1
        if self.__left <= 0:
            self.leave_splash()
            return

        self.query_one("#prompt", Static).update(self.prompt_text())
        self.set_timer(1.0, self.tick_countdown)

    def leave_splash(self) -> None:
        if self.__done:
            return

        self.__done = True
        self.dismiss()

    def on_key(self, event: events.Key) -> None:
        self.leave_splash()
        event.stop()
