"""Compose and save a new or reply message."""

from datetime import datetime

from golded_ftn import FtnAddress, OutgoingMessage
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Input, Static, TextArea

from ui.status import StatusBar
from ui.title import area_title_line

def open_write_screen(app, session, callback) -> None:
    session.start_draft_message()

    if session.draft_message() is None:
        return

    app.push_screen(WriteMessageScreen(session), callback)

def open_reply_screen(
    app,
    session,
    body_for_quote: str,
    callback,
    subject_for_reply: str | None = None,
) -> None:
    session.start_reply_draft(body_for_quote, subject_for_reply)

    if session.draft_message() is None:
        return

    app.push_screen(WriteMessageScreen(session), callback)

class DiscardDialog(ModalScreen[bool]):
    """Ask whether to discard the draft.

    Backdrop alpha lives in GoldED CSS (ModalScreen). App-wide
    `Screen { background: $ged-bg; }` would otherwise paint it solid.
    True `transparent` skips the screen underneath and shows the app only.
    """

    DEFAULT_CSS = """
    DiscardDialog {
        align: center middle;
    }

    #discard-box {
        width: 34;
        height: auto;
        border: heavy $ged-title;
        background: $ged-bg;
        color: $ged-fg;
        padding: 1 2;
        layout: vertical;
    }

    #discard-title {
        width: 100%;
        color: $ged-title;
        text-align: center;
    }

    #discard-keys {
        width: 100%;
        color: $ged-meta;
        text-align: center;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "No"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id = "discard-box"):
            yield Static("Discard draft?", id = "discard-title")
            yield Static("Y / N", id = "discard-keys")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

class WriteMessageScreen(Screen):
    AUTO_FOCUS = "#subject"

    DEFAULT_CSS = """
    WriteMessageScreen {
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

    #msg-line {
        height: 1;
        width: 100%;
        color: $ged-meta;
        padding: 0;
    }

    #fields {
        height: auto;
        padding: 0;
        background: $ged-bg;
        layout: vertical;
    }

    .field-row {
        height: 1;
        width: 100%;
        layout: horizontal;
        background: $ged-bg;
    }

    .field-label {
        width: 8;
        color: $ged-meta;
        padding: 0;
    }

    .field-row Input {
        width: 32;
        max-width: 32;
        background: $ged-bg;
        color: $ged-fg;
        border: none !important;
        padding: 0;
        height: 1;
        margin: 0;
        background-tint: $ged-bg 0%;
    }

    .field-row #subject {
        width: 1fr;
        max-width: 100%;
    }

    .field-row Input:focus {
        background: $ged-bg;
        color: $ged-title;
        background-tint: $ged-bg 0%;
    }

    .field-row Input > .input--cursor {
        background: $ged-title;
        color: $ged-bg;
    }

    .field-row Input > .input--selection {
        background: $ged-cursor-bg;
        color: $ged-cursor-fg;
    }

    #from-addr {
        width: 18;
        color: $ged-meta;
        padding: 0 0 0 1;
    }

    .field-row #to-addr {
        width: 18;
        max-width: 18;
    }

    .field-gap {
        width: 1fr;
        height: 1;
    }

    #from-date {
        width: auto;
        color: $ged-meta;
        padding: 0 1 0 0;
        content-align: right middle;
    }

    #sep {
        height: 1;
        width: 100%;
        padding: 0;
        color: $ged-line;
    }

    #body {
        height: 1fr;
        background: $ged-bg;
        color: $ged-body;
        border: none;
        padding: 0;
        margin: 0;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        Binding("ctrl+s,super+s", "save", "Save", priority = True),
        Binding("f2", "save", "Save", priority = True),
        Binding("up", "focus_up", "Up", priority = True),
        Binding("down", "focus_down", "Down", priority = True),
    ]

    def __init__(self, session) -> None:
        super().__init__()
        self.__session = session

    def compose(self) -> ComposeResult:
        yield Static("", id = "title", markup = True)
        yield Static("", id = "msg-line")
        yield Vertical(
            Horizontal(
                Static(" From :", classes = "field-label"),
                Input(id = "from-name", select_on_focus = False),
                Static("", id = "from-addr"),
                Static("", classes = "field-gap"),
                Static("", id = "from-date"),
                classes = "field-row",
            ),
            Horizontal(
                Static(" To   :", classes = "field-label"),
                Input(id = "to-name", select_on_focus = False),
                Input("", id = "to-addr", select_on_focus = False),
                classes = "field-row",
            ),
            Horizontal(
                Static(" Subj :", classes = "field-label"),
                Input(id = "subject", select_on_focus = False),
                classes = "field-row",
            ),
            id = "fields",
        )
        yield Static("", id = "sep", markup = True)
        yield TextArea(id = "body")
        yield StatusBar()

    def on_mount(self) -> None:
        draft = self.__session.draft_message()

        if draft is None:
            self.dismiss(None)
            return

        self.query_one("#from-name", Input).value = draft.from_name
        self.query_one("#to-name", Input).value = draft.to_name
        self.query_one("#subject", Input).value = draft.subject
        self.query_one("#body", TextArea).text = draft.body_text

        self.show_header(reset_to_address = True)
        self.update_status("")

    def on_resize(self) -> None:
        self.show_header(reset_to_address = False)

    def apply_theme(self) -> None:
        self.show_header(reset_to_address = False)

    def show_header(self, reset_to_address: bool = False) -> None:
        area_code = self.__session.draft_area()
        if area_code is None:
            area_code = self.__session.selected_area()

        width = self.size.width
        if width < 40:
            width = 80

        line = self.app.ged_color("line")
        title = area_title_line(
            self.__session.area_name(area_code),
            area_code,
            width,
            line,
            self.app.ged_color("title"),
        )
        self.query_one("#title", Static).update(title)

        total = len(self.__session.messages())
        position = total + 1
        self.query_one("#msg-line", Static).update(
            f" Msg  : {position} of {position}"
        )

        draft = self.__session.draft_message()
        from_address = ""
        to_address = ""
        if draft is not None:
            if draft.from_address is not None:
                from_address = str(draft.from_address)
            if draft.to_address is not None:
                to_address = str(draft.to_address)
        self.query_one("#from-addr", Static).update(from_address)
        to_addr = self.query_one("#to-addr", Input)
        if self.draft_is_netmail():
            to_addr.disabled = False
            if reset_to_address:
                to_addr.value = to_address
        else:
            to_addr.disabled = True
            if reset_to_address:
                to_addr.value = ""

        now = datetime.now().strftime("%d %b %y  %H:%M:%S")
        self.query_one("#from-date", Static).update(now)

        after = width - 1
        if after < 1:
            after = 1
        sep = f"[{line}]{'─' * after}[/]"
        self.query_one("#sep", Static).update(sep)

    def draft_is_netmail(self) -> bool:
        area = self.__session.draft_area()
        if area is None:
            return False

        return self.__session.area_kind(area) == "netmail"

    def read_to_address(self) -> tuple[FtnAddress | None, str | None]:
        if not self.draft_is_netmail():
            draft = self.__session.draft_message()
            if draft is None:
                return None, None
            return draft.to_address, None

        text = self.query_one("#to-addr", Input).value.strip()
        if text == "":
            return None, None

        try:
            return FtnAddress.from_string(text), None
        except ValueError as error:
            return None, str(error)

    def update_status(self, error: str) -> None:
        draft = self.__session.draft_message()
        mode = "Write"
        if draft is not None and draft.reply_to_msgno is not None:
            mode = "Reply"

        text = mode
        if error != "":
            text = f"{mode} - {error}"

        self.query_one(StatusBar).set_middle(text)

    def action_focus_up(self) -> None:
        focused = self.focused
        if focused is None:
            return

        if focused.id == "body":
            body = self.query_one("#body", TextArea)
            row = body.cursor_location[0]
            if row > 0:
                body.action_cursor_up()
                return
            self.query_one("#subject", Input).focus()
            return

        if focused.id == "subject":
            if self.draft_is_netmail():
                self.query_one("#to-addr", Input).focus()
            else:
                self.query_one("#to-name", Input).focus()
        elif focused.id == "to-addr":
            self.query_one("#to-name", Input).focus()
        elif focused.id == "to-name":
            self.query_one("#from-name", Input).focus()

    def action_focus_down(self) -> None:
        focused = self.focused
        if focused is None:
            return

        if focused.id == "from-name":
            self.query_one("#to-name", Input).focus()
        elif focused.id == "to-name":
            if self.draft_is_netmail():
                self.query_one("#to-addr", Input).focus()
            else:
                self.query_one("#subject", Input).focus()
        elif focused.id == "to-addr":
            self.query_one("#subject", Input).focus()
        elif focused.id == "subject":
            self.query_one("#body", TextArea).focus()
        elif focused.id == "body":
            self.query_one("#body", TextArea).action_cursor_down()

    def sync_draft(self) -> str | None:
        draft = self.__session.draft_message()
        reply_to = None
        from_address = None
        previous_to_address = None
        if draft is not None:
            reply_to = draft.reply_to_msgno
            from_address = draft.from_address
            previous_to_address = draft.to_address

        to_address, parse_error = self.read_to_address()
        if parse_error is not None:
            to_address = previous_to_address

        message = OutgoingMessage(
            from_name = self.query_one("#from-name", Input).value,
            to_name = self.query_one("#to-name", Input).value,
            subject = self.query_one("#subject", Input).value,
            body_text = self.query_one("#body", TextArea).text,
            reply_to_msgno = reply_to,
            from_address = from_address,
            to_address = to_address,
        )
        self.__session.set_draft_message(message)

        return parse_error

    def action_save(self) -> None:
        parse_error = self.sync_draft()
        if parse_error is not None:
            self.update_status(parse_error)
            return

        try:
            msgno = self.__session.save_draft_message()
        except Exception as error:
            self.update_status(str(error))
            return

        self.dismiss(msgno)

    def after_discard(self, confirmed: bool | None) -> None:
        self.update_status("")

        if confirmed:
            self.__session.discard_draft_message()
            self.dismiss(None)
            return

        self.query_one("#subject", Input).focus()

    def action_go_back(self) -> None:
        if self.__session.draft_message() is None:
            self.dismiss(None)
            return

        self.sync_draft()
        self.update_status("Discard draft? Y/N")
        self.app.push_screen(DiscardDialog(), self.after_discard)
