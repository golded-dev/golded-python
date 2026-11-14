"""Shared DataTable list frame with GoldED pagebar."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static

from golded.ui.pagebar import fit_list_end, paint_pagebar
from golded.ui.status import StatusBar


class ListScreen(Screen):
    TABLE_ID = "list"
    PAGEBAR_BORDER = "border"

    def table(self) -> DataTable:
        return self.query_one(f"#{self.TABLE_ID}", DataTable)

    def action_page_down(self) -> None:
        self.table().action_page_down()
        self.sync_pagebar()

    def action_page_up(self) -> None:
        self.table().action_page_up()
        self.sync_pagebar()

    def compose_list(self, title_markup: bool = False) -> ComposeResult:
        yield Static("", id="title", markup=title_markup)
        yield Horizontal(
            Vertical(
                DataTable(id=self.TABLE_ID),
                Static("", id="list-end"),
                Static("", id="list-pad"),
                id="list-main",
            ),
            Vertical(
                Static("┐", id="pagebar-top"),
                Static("", id="pagebar"),
                Static("┘", id="pagebar-bot"),
                id="pagebar-col",
            ),
            id="list-frame",
        )
        yield StatusBar()

    def sync_pagebar(self) -> None:
        table = self.table()
        paint_pagebar(
            self.query_one("#pagebar", Static),
            table.row_count,
            table.size.height,
            int(table.scroll_y),
            self.app.ged_color(self.PAGEBAR_BORDER),
            self.app.ged_color("status-fg"),
        )

    def fit_list_end(self) -> None:
        fit_list_end(
            self.table(),
            self.query_one("#list-main", Vertical),
            self.query_one("#list-end", Static),
            self.query_one("#list-pad", Static),
        )

    def on_scroll(self, event) -> None:
        if event.node.id == self.TABLE_ID:
            self.sync_pagebar()
