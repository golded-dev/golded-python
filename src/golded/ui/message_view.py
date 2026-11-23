"""One message, scrollable."""

from golded_ftn import ParsedMessage
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from golded.logic.display_text import for_display
from golded.logic.quote import has_golded_tagline, split_body_at_tagline
from golded.logic.session import Session
from golded.ui.pagebar import paint_pagebar
from golded.ui.status import StatusBar
from golded.ui.theme import ged_color
from golded.ui.title import area_title_line
from golded.ui.write_message import open_reply_screen, open_write_screen


class MessageViewScreen(Screen[int | None]):
    DEFAULT_CSS = """
    MessageViewScreen {
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

    #meta {
        height: auto;
        color: $ged-meta;
        padding: 0;
    }

    #sep {
        height: 1;
        padding: 0;
        color: $ged-line;
    }

    #body-frame {
        height: 1fr;
        layout: horizontal;
        background: $ged-bg;
    }

    #body-scroll {
        width: 1fr;
        height: 1fr;
        scrollbar-size-vertical: 0;
        scrollbar-size-horizontal: 0;
    }

    #body-main {
        color: $ged-body;
        padding: 0;
    }

    #body-tag {
        color: $ged-tag;
        padding: 0;
    }

    #pagebar {
        width: 1;
        min-width: 1;
        max-width: 1;
        height: 1fr;
        color: $ged-status-fg;
        background: $ged-border;
        text-align: center;
        overflow: hidden;
        padding: 0;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        Binding("right", "next_message", "Next", priority=True),
        Binding("left", "previous_message", "Prev", priority=True),
        Binding("shift+right", "next_subject_message", "Next subject", priority=True),
        Binding(
            "shift+left", "previous_subject_message", "Prev subject", priority=True
        ),
        ("space", "page_down", "Page down"),
        ("shift+space", "page_up", "Page up"),
        ("m", "toggle_mojibake_repair", "Mojibake"),
        ("w", "write_message", "Write"),
        ("r", "reply_message", "Reply"),
    ]

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.__session = session
        self.__repair_mojibake = False

    def action_go_back(self) -> None:
        self.dismiss()

    def action_write_message(self) -> None:
        open_write_screen(self.app, self.__session, self.after_write)

    def action_reply_message(self) -> None:
        message = self.__session.current_message()
        if message is None:
            return

        repair = self.__repair_mojibake
        body = for_display(message.body_text, repair)
        subject = for_display(message.subject, repair)
        open_reply_screen(
            self.app,
            self.__session,
            body,
            self.after_write,
            subject,
        )

    def after_write(self, result: int | None = None) -> None:
        if result is None:
            self.show_current_message()
            return

        self.dismiss(result)

    def action_toggle_mojibake_repair(self) -> None:
        self.__repair_mojibake = not self.__repair_mojibake
        self.show_current_message()

    def action_next_message(self) -> None:
        self.__session.next_message()
        self.show_current_message()

    def action_previous_message(self) -> None:
        self.__session.previous_message()
        self.show_current_message()

    def action_next_subject_message(self) -> None:
        self.__session.next_subject_message()
        self.show_current_message()

    def action_previous_subject_message(self) -> None:
        self.__session.previous_subject_message()
        self.show_current_message()

    def action_page_down(self) -> None:
        self.query_one("#body-scroll", VerticalScroll).scroll_page_down()
        self.sync_pagebar()

    def action_page_up(self) -> None:
        self.query_one("#body-scroll", VerticalScroll).scroll_page_up()
        self.sync_pagebar()

    def compose(self) -> ComposeResult:
        yield Static("", id="title", markup=True)
        yield Static("", id="meta", markup=False)
        yield Static("", id="sep", markup=True)
        yield Horizontal(
            VerticalScroll(
                Static("", id="body-main", markup=False),
                Static("", id="body-tag", markup=False),
                id="body-scroll",
            ),
            Static("", id="pagebar"),
            id="body-frame",
        )
        yield StatusBar()

    def on_mount(self) -> None:
        body = self.query_one("#body-scroll", VerticalScroll)
        self.watch(body, "scroll_y", self.on_body_scroll_y)
        self.show_current_message()
        self.call_after_refresh(self.sync_pagebar)

    def on_resize(self) -> None:
        self.show_current_message()

    def apply_theme(self) -> None:
        self.show_current_message()
        self.sync_pagebar()

    def on_body_scroll_y(self, old_value: float, new_value: float) -> None:
        self.sync_pagebar()

    def sync_pagebar(self) -> None:
        body = self.query_one("#body-scroll", VerticalScroll)
        paint_pagebar(
            self.query_one("#pagebar", Static),
            body.virtual_size.height,
            body.size.height,
            int(body.scroll_y),
            ged_color(self.app, "border"),
            ged_color(self.app, "status-fg"),
        )

    def show_current_message(self) -> None:
        message = self.__session.current_message()

        if message is None:
            return

        width = self.size.width
        if width < 40:
            width = 80

        self.show_title(width)
        self.show_meta(message, width)
        self.show_separator(message, width)
        self.show_body(message)
        self.show_status(message)
        self.call_after_refresh(self.sync_pagebar)

    def show_title(self, width: int) -> None:
        area_code = self.__session.selected_area()
        assert area_code is not None, "message view without a selected area"
        name = self.__session.area_name(area_code)
        if self.__session.readonly():
            name = f"Read-only · {name}"
        title = area_title_line(
            name,
            area_code,
            width,
            ged_color(self.app, "line"),
            ged_color(self.app, "title"),
        )
        self.query_one("#title", Static).update(title)

    def show_meta(self, message: ParsedMessage, width: int) -> None:
        messages = self.__session.messages()
        total = len(messages)
        index = self.__session.current_message_index()
        assert index is not None, "message view without a current message"
        position = index + 1

        repair = self.__repair_mojibake
        from_name = for_display(message.from_name, repair)
        to_name = for_display(message.to_name, repair)
        subject = for_display(message.subject, repair)

        from_address = self.display_address(message.from_address)
        controls = message.control_lines
        if (
            from_address == ""
            and controls is not None
            and controls.origin_address is not None
        ):
            from_address = str(controls.origin_address)

        to_address = self.display_address(message.to_address)

        date_line = ""
        if message.posted_at is not None:
            date_line = message.posted_at.strftime("%d %b %y  %H:%M:%S ")

        from_line = self.party_line("From ", from_name, from_address, date_line, width)
        to_line = self.party_line("To   ", to_name, to_address, "", width)

        meta = (
            f" Msg  : {position} of {total}\n{from_line}\n{to_line}\n Subj : {subject}"
        )
        self.query_one("#meta", Static).update(meta)

    def show_separator(self, message: ParsedMessage, width: int) -> None:
        size = len(message.body_text.encode("utf-8"))
        size_text = str(size)
        after = width - 1 - len(size_text)
        if after < 8:
            after = 8

        line = ged_color(self.app, "line")
        title_color = ged_color(self.app, "title")
        sep = f"[{line}]─[/][{title_color}]{size_text}[/][{line}]{'─' * after}[/]"
        self.query_one("#sep", Static).update(sep)

    def show_body(self, message: ParsedMessage) -> None:
        body_text = for_display(message.body_text, self.__repair_mojibake)
        main_text, tag_text = split_body_at_tagline(body_text)
        self.query_one("#body-main", Static).update(main_text)
        self.query_one("#body-tag", Static).update(tag_text)

    def show_status(self, message: ParsedMessage) -> None:
        messages = self.__session.messages()
        total = len(messages)
        index = self.__session.current_message_index()
        assert index is not None, "message view without a current message"
        position = index + 1
        left = total - position

        status = f"Read - Msg {position} of {total} ({left} left)"
        if self.__repair_mojibake:
            status = f"{status} | Mojibake"

        status_bar = self.query_one(StatusBar)
        status_bar.set_middle(status)
        status_bar.set_product(squared=has_golded_tagline(message.body_text))

    def display_address(self, address: str | None) -> str:
        if address is None:
            return ""

        return str(address)

    def party_line(
        self,
        label: str,
        name: str,
        address: str,
        date_text: str,
        width: int,
    ) -> str:
        left = f" {label}: {name}"
        line = left

        if address != "":
            while len(line) < 40:
                line = line + " "
            if len(line) > 40:
                line = line + "  "
            line = line + address

        if date_text != "":
            gap = width - len(line) - len(date_text)
            if gap < 2:
                gap = 2
            line = line + (" " * gap) + date_text

        return line
