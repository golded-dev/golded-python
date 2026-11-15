"""Bottom status bar."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from golded.logic.version import PRODUCT, PRODUCT_NAME, VERSION


class StatusBar(Horizontal):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        max-height: 1;
        width: 100%;
        background: $ged-status-bg;
        color: $ged-status-fg;
        overflow: hidden;
    }

    StatusBar > Static {
        height: 1;
        max-height: 1;
        overflow: hidden;
        background: $ged-status-bg;
        color: $ged-status-fg;
    }

    #status-left {
        width: auto;
    }

    #status-middle {
        width: 1fr;
    }

    #status-right {
        width: auto;
        content-align: right middle;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="status")

    def compose(self) -> ComposeResult:
        yield Static(f" {PRODUCT} | ", id="status-left")
        # Carries area codes and error text, which may contain [brackets].
        yield Static("", id="status-middle", markup=False)
        yield Static("", id="status-right")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_clock)
        self.update_clock()

    def set_middle(self, text: str) -> None:
        self.query_one("#status-middle", Static).update(text)

    def set_product(self, squared: bool = False) -> None:
        if squared:
            text = f" {PRODUCT_NAME}²{VERSION} | "
        else:
            text = f" {PRODUCT} | "
        self.query_one("#status-left", Static).update(text)

    def update_clock(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.query_one("#status-right", Static).update(f"| {now} ")
