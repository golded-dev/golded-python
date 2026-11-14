"""Area list screen."""

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.geometry import Size
from textual.widgets import DataTable, Static

from golded.logic.session import Session
from golded.ui.list_screen import ListScreen
from golded.ui.message_list import MessageListScreen
from golded.ui.status import StatusBar


class AreaListScreen(ListScreen):
    TABLE_ID = "areas"
    PAGEBAR_BORDER = "border"

    DEFAULT_CSS = """
    AreaListScreen {
        background: $ged-bg;
        layout: vertical;
    }

    #title {
        height: 1;
        width: 100%;
        padding: 0 1;
        color: $ged-prompt;
        background: $ged-bg;
    }

    #list-frame {
        height: 1fr;
        layout: horizontal;
        background: $ged-bg;
    }

    #list-main {
        width: 1fr;
        height: 1fr;
        border-top: solid $ged-border;
        border-left: solid $ged-border;
        border-bottom: solid $ged-border;
        border-right: none;
        background: $ged-bg;
        layout: vertical;
    }

    #areas {
        height: auto;
        max-height: 100%;
        border: none;
        background: $ged-bg;
        overflow-x: hidden;
        scrollbar-size-vertical: 0;
        scrollbar-size-horizontal: 0;
    }

    #list-end {
        height: 1;
        color: $ged-endline;
    }

    #list-pad {
        height: 1fr;
    }

    #pagebar-col {
        width: 1;
        min-width: 1;
        max-width: 1;
        height: 1fr;
        layout: vertical;
        background: $ged-bg;
    }

    #pagebar-top,
    #pagebar-bot {
        height: 1;
        width: 1;
        color: $ged-border;
        background: $ged-bg;
        text-align: center;
    }

    #pagebar {
        width: 1;
        height: 1fr;
        color: $ged-status-fg;
        background: $ged-border;
        text-align: center;
        overflow: hidden;
        padding: 0;
    }
    """

    BINDINGS = [
        ("space", "page_down", "Page down"),
        ("shift+space", "page_up", "Page up"),
    ]

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.__session = session
        self.__filter = ""
        self.__rows: list[tuple[int, str, int, str]] = []

    def compose(self) -> ComposeResult:
        yield from self.compose_list(title_markup=False)

    def on_mount(self) -> None:
        self.follow_table_scroll()
        table = self.table()
        table.cursor_type = "row"
        table.add_column(Text("Area", justify="right"), width=4)
        table.add_column("Description", width=40)
        table.add_column(Text("Msgs", justify="right"), width=6)
        table.add_column("EchoID", width=16)

        self.reload_rows()
        self.show_title()
        self.fill_table()
        self.call_after_refresh(self.fit_layout)

    def on_screen_resume(self, event: events.ScreenResume) -> None:
        self.reload_rows()
        self.fill_table()
        self.fit_layout()

    def reload_rows(self) -> None:
        self.__rows = []
        number = 1

        for area in self.__session.areas():
            count = self.__session.message_count(area.code)
            self.__rows.append((number, area.name, count, area.code))
            number = number + 1

    def on_resize(self) -> None:
        self.fit_layout()

    def apply_theme(self) -> None:
        self.sync_pagebar()

    def on_key(self, event: events.Key) -> None:
        if event.key == "backspace":
            if self.__filter == "":
                return

            self.__filter = self.__filter[:-1]
            self.show_title()
            self.fill_table()
            self.fit_layout()
            event.stop()
            return

        if event.character is None:
            return

        if not event.character.isprintable():
            return

        if event.key == "space" or event.key == "enter":
            return

        self.__filter = self.__filter + event.character
        self.show_title()
        self.fill_table()
        self.fit_layout()
        event.stop()

    def show_title(self) -> None:
        self.query_one("#title", Static).update(f">>Pick New Area: {self.__filter}")

    def area_matches(self, name: str, code: str) -> bool:
        if self.__filter == "":
            return True

        needle = self.__filter.lower()

        if needle in name.lower():
            return True

        if needle in code.lower():
            return True

        return False

    def fill_table(self) -> None:
        table = self.table()
        table.clear()

        for number, name, count, code in self.__rows:
            if self.area_matches(name, code):
                table.add_row(
                    Text(str(number), justify="right"),
                    name,
                    Text(str(count), justify="right"),
                    code,
                )

        if table.row_count > 0:
            table.move_cursor(row=0)

    def fit_layout(self) -> None:
        self.fit_columns()
        self.fit_list_end()
        self.sync_pagebar()

    def fit_columns(self) -> None:
        table = self.table()

        if table.size.width <= 0:
            return

        if len(table.columns) < 4:
            return

        area_width = 4
        msgs_width = 6
        padding = table.cell_padding * 2 * 4
        free = table.size.width - padding - 1 - area_width - msgs_width

        if free < 36:
            free = 36

        description_width = (free * 3) // 4
        echoid_width = free - description_width

        columns = table.ordered_columns
        columns[0].width = area_width
        columns[1].width = description_width
        columns[2].width = msgs_width
        columns[3].width = echoid_width

        total_width = 0
        for column in columns:
            total_width = total_width + column.get_render_width(table)

        table.virtual_size = Size(total_width, table.virtual_size.height)
        table.refresh()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "areas":
            return

        if not event.data_table.is_valid_row_index(event.cursor_row):
            return

        row = event.data_table.get_row_at(event.cursor_row)
        text = f"{row[3]}: {row[2]} msgs"
        self.query_one(StatusBar).set_middle(text)
        self.sync_pagebar()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "areas":
            return

        row = event.data_table.get_row(event.row_key)
        area = row[3]
        self.__session.select_area(area)
        self.app.push_screen(MessageListScreen(self.__session))
