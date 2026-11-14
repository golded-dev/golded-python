import unittest

from textual.app import App, ComposeResult
from textual.widgets import Static

from golded.logic.display_text import literal_text


class MarkupScreen(App[None]):
    def compose(self) -> ComposeResult:
        yield Static("", id="meta", markup=False)
        yield Static("", id="body", markup=False)


class MessageMarkupTests(unittest.IsolatedAsyncioTestCase):
    async def test_static_shows_literal_brackets(self) -> None:
        app = MarkupScreen()
        async with app.run_test() as pilot:
            sample = "[b]Bogstavelig tekst[/b]"
            app.query_one("#meta", Static).update(f" Subj : {sample}")
            app.query_one("#body", Static).update(sample)
            await pilot.pause()

            meta = app.query_one("#meta", Static)
            body = app.query_one("#body", Static)
            self.assertIn("[b]", str(meta.render()))
            self.assertIn("[/b]", str(meta.render()))
            self.assertIn("[b]", str(body.render()))
            self.assertNotIn("bold", str(body.render()).lower())

    def test_literal_text_is_not_markup(self) -> None:
        text = literal_text("[b]x[/b]")
        self.assertEqual(text.plain, "[b]x[/b]")


if __name__ == "__main__":
    unittest.main()
