"""Message list for the selected area."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.geometry import Size
from textual.widgets import DataTable, Static

from golded.logic.display_text import literal_text
from golded.logic.session import Session
from golded.logic.thread_tree import format_branch_prefix
from golded.ui.list_screen import ListScreen
from golded.ui.message_view import MessageViewScreen
from golded.ui.status import StatusBar
from golded.ui.theme import ged_color
from golded.ui.title import area_title_line
from golded.ui.write_message import open_write_screen


class MessageListScreen(ListScreen):
    TABLE_ID = "messages"
    PAGEBAR_BORDER = "msg-border"

    DEFAULT_CSS = """
    MessageListScreen {
        background: $ged-bg;
        layout: vertical;
    }

    #title {
        height: 1;
        width: 100%;
        padding: 0;
        color: $ged-line;
        overflow: hidden;
    }

    #list-frame {
        height: 1fr;
        layout: horizontal;
        background: $ged-bg;
    }

    #list-main {
        width: 1fr;
        height: 1fr;
        border-top: solid $ged-msg-border;
        border-left: solid $ged-msg-border;
        border-bottom: solid $ged-msg-border;
        border-right: none;
        border-subtitle-align: center;
        border-subtitle-color: $ged-subtitle;
        background: $ged-bg;
        layout: vertical;
    }

    #messages {
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
        color: $ged-msg-border;
        background: $ged-bg;
        text-align: center;
    }

    #pagebar {
        width: 1;
        height: 1fr;
        color: $ged-status-fg;
        background: $ged-msg-border;
        text-align: center;
        overflow: hidden;
        padding: 0;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("w", "write_message", "Write"),
        ("t", "toggle_threaded", "Thread"),
        ("space", "page_down", "Page down"),
        ("shift+space", "page_up", "Page up"),
    ]

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.__session = session

    def compose(self) -> ComposeResult:
        yield from self.compose_list(title_markup=True)

    def action_go_back(self) -> None:
        self.dismiss()

    def action_open_message(self) -> None:
        table = self.table()

        if not table.is_valid_row_index(table.cursor_row):
            return

        row = table.get_row_at(table.cursor_row)
        msgno = int(row[0])
        self.__session.select_message(msgno)
        self.app.push_screen(
            MessageViewScreen(self.__session),
            self.after_message_view,
        )

    def action_write_message(self) -> None:
        open_write_screen(self.app, self.__session, self.after_write)

    def action_toggle_threaded(self) -> None:
        current = None
        table = self.table()
        if table.is_valid_row_index(table.cursor_row):
            row = table.get_row_at(table.cursor_row)
            current = int(row[0])

        self.__session.toggle_threaded_list()
        self.reload_messages()

        if current is not None:
            self.select_msgno(current)

    def after_message_view(self, result: int | None = None) -> None:
        if result is not None:
            self.reload_messages()
            self.__session.select_message(result)
            self.select_msgno(result)
            return

        current = self.__session.current_message()
        if current is not None:
            self.select_msgno(current.msgno)
            return

        self.update_subject_line()
        self.sync_pagebar()

    def after_write(self, result: int | None = None) -> None:
        self.reload_messages()

        if result is not None:
            self.__session.select_message(result)
            self.select_msgno(result)
            return

        self.update_subject_line()
        self.sync_pagebar()

    def on_mount(self) -> None:
        self.follow_table_scroll()
        self.show_title()

        table = self.table()
        table.cursor_type = "row"
        table.add_column("Msg", width=5)
        table.add_column("From", width=20)
        table.add_column("To", width=20)
        table.add_column("Subject", width=38)
        table.add_column("Written", width=9)

        self.fill_messages()
        self.call_after_refresh(self.fit_layout)

    def fill_messages(self) -> None:
        table = self.table()
        table.clear()

        for row in self.__session.message_rows():
            message = row.message
            written = ""
            if message.posted_at is not None:
                written = message.posted_at.strftime("%d %b %y")

            from_name = message.from_name
            if self.__session.threaded_list():
                prefix = format_branch_prefix(row.branch_path)
                if row.broken:
                    from_name = "!" + prefix + from_name
                else:
                    from_name = prefix + from_name

            table.add_row(
                str(message.msgno),
                literal_text(from_name),
                literal_text(message.to_name),
                literal_text(message.subject),
                written,
            )

    def reload_messages(self) -> None:
        self.fill_messages()
        self.show_title()
        self.fit_layout()

    def select_msgno(self, msgno: int) -> None:
        table = self.table()

        for index in range(table.row_count):
            row = table.get_row_at(index)
            if int(row[0]) == msgno:
                table.move_cursor(row=index)
                self.update_subject_line()
                self.sync_pagebar()
                return

    def on_resize(self) -> None:
        self.fit_layout()

    def apply_theme(self) -> None:
        self.show_title()
        self.sync_pagebar()

    def show_title(self) -> None:
        area_code = self.__session.selected_area()
        assert area_code is not None, "message list without a selected area"
        title = area_title_line(
            self.__session.area_name(area_code),
            area_code,
            self.size.width,
            ged_color(self.app, "line"),
            ged_color(self.app, "title"),
        )
        self.query_one("#title", Static).update(title)

    def fit_layout(self) -> None:
        self.fit_columns()
        self.fit_list_end()
        self.update_subject_line()
        self.sync_pagebar()

    def fit_columns(self) -> None:
        table = self.table()

        if table.size.width <= 0:
            return

        if len(table.columns) < 5:
            return

        msg_width = 5
        written_width = 9
        padding = table.cell_padding * 2 * 5
        free = table.size.width - padding - 1 - msg_width - written_width

        if free < 24:
            free = 24

        if self.__session.threaded_list():
            from_width = free // 3
            to_width = free // 3
            subject_width = free - from_width - to_width
        else:
            from_width = free // 4
            to_width = free // 4
            subject_width = free - from_width - to_width

        columns = table.ordered_columns
        columns[0].width = msg_width
        columns[1].width = from_width
        columns[2].width = to_width
        columns[3].width = subject_width
        columns[4].width = written_width

        total_width = 0
        for column in columns:
            total_width = total_width + column.get_render_width(table)

        table.virtual_size = Size(total_width, table.virtual_size.height)
        table.refresh()

    def update_subject_line(self) -> None:
        table = self.table()
        main = self.query_one("#list-main", Vertical)

        if not table.is_valid_row_index(table.cursor_row):
            main.border_subtitle = None
            return

        row = table.get_row_at(table.cursor_row)
        subject = row[3]
        if isinstance(subject, str):
            main.border_subtitle = literal_text(subject)
        else:
            main.border_subtitle = subject

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "messages":
            return

        if event.row_key is None:
            return

        total = event.data_table.row_count
        position = event.cursor_row + 1
        left = total - position
        text = f"Lister - Msg {position} of {total} ({left} left)"
        self.query_one(StatusBar).set_middle(text)
        self.update_subject_line()
        self.sync_pagebar()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "messages":
            return

        self.action_open_message()
