"""Textual application shell."""

from textual.app import App

from golded.data.store import open_message_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig
from golded.ui.area_list import AreaListScreen
from golded.ui.message_list import MessageListScreen
from golded.ui.message_view import MessageViewScreen
from golded.ui.splash import SplashScreen
from golded.ui.theme import DEFAULT_THEME, THEMES
from golded.ui.write_message import WriteMessageScreen

class GoldED(App):
    CSS = """
    Screen {
        background: $ged-bg;
    }

    ModalScreen {
        background: $ged-bg 1%;
    }

    #logo {
        color: $ged-logo;
        width: auto;
        height: auto;
    }

    DataTable {
        height: 1fr;
        background: $ged-bg;
        color: $ged-fg;
        border: none;
        overflow-x: hidden;
        scrollbar-background: $ged-bg;
        scrollbar-color: $ged-scroll;
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 0;
    }

    DataTable:focus {
        background-tint: $ged-bg 0%;
    }

    AreaListScreen DataTable,
    MessageListScreen DataTable {
        border: none;
        scrollbar-size-vertical: 0;
        scrollbar-size-horizontal: 0;
    }

    AreaListScreen DataTable > ScrollBar,
    MessageListScreen DataTable > ScrollBar,
    MessageViewScreen #body-scroll > ScrollBar {
        display: none;
    }

    MessageViewScreen #body-scroll {
        scrollbar-size-vertical: 0;
        scrollbar-size-horizontal: 0;
    }

    VerticalScroll {
        height: 1fr;
    }

    DataTable > .datatable--header,
    DataTable:focus > .datatable--header {
        background: $ged-bg;
        color: $ged-header;
        text-style: bold;
        background-tint: $ged-bg 0%;
    }

    DataTable > .datatable--even-row,
    DataTable > .datatable--odd-row {
        background: $ged-bg;
        color: $ged-fg;
    }

    DataTable > .datatable--hover {
        background: $ged-bg;
        color: $ged-fg;
    }

    DataTable > .datatable--cursor {
        background: $ged-cursor-bg;
        color: $ged-cursor-fg;
    }

    DataTable:focus > .datatable--cursor {
        background: $ged-cursor-bg;
        color: $ged-cursor-fg;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("f9", "toggle_theme", "Theme"),
    ]

    def __init__(self, session, theme_name: str = DEFAULT_THEME) -> None:
        super().__init__()
        self.__session = session

        for theme in THEMES:
            self.register_theme(theme)

        self.theme = theme_name

    def get_theme_variable_defaults(self) -> dict:
        return dict(THEMES[0].variables)

    def ged_color(self, name: str) -> str:
        theme = self.get_theme(self.theme)

        return theme.variables[f"ged-{name}"]

    def on_mount(self) -> None:
        self.push_screen(AreaListScreen(self.__session))
        self.push_screen(SplashScreen())

    def action_toggle_theme(self) -> None:
        self.theme = "dark" if self.theme == "light" else "light"

        self.refresh_themed_screens()

    def refresh_themed_screens(self) -> None:
        for screen in self.screen_stack:
            if isinstance(
                screen,
                (
                    AreaListScreen,
                    MessageListScreen,
                    MessageViewScreen,
                    WriteMessageScreen,
                ),
            ):
                screen.apply_theme()

def run(
    database_path: str = "messages.sqlite3",
    theme_name: str = DEFAULT_THEME,
    user_config: UserConfig | None = None,
) -> None:
    store = open_message_store(database_path)
    session = Session(store, user_config)
    GoldED(session, theme_name).run()
