"""Drive the Textual app headless against a seeded database."""

import tempfile
import unittest

from golded_ftn import FtnAddress, OutgoingMessage
from textual.pilot import Pilot
from textual.widgets import Input, Static, TextArea

from golded.data.area import Area
from golded.data.store import create_message_store, open_message_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig
from golded.ui.app import GoldED
from golded.ui.area_list import AreaListScreen
from golded.ui.message_list import MessageListScreen
from golded.ui.message_view import MessageViewScreen
from golded.ui.splash import SplashScreen
from golded.ui.write_message import DiscardDialog, WriteMessageScreen
from seed_demo import seed_database

SIZE = (100, 30)


class AppSmokeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        path = f"{self.__tmp.name}/test.sqlite3"
        seed_database(path)
        self.path = path
        config = UserConfig(
            from_name="Tester", from_address=FtnAddress.from_string("2:236/777")
        )
        self.session = Session(open_message_store(path), config)
        self.app = GoldED(self.session, "dark")

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    async def open_area(self, pilot: Pilot[None], letters: str) -> None:
        await pilot.press("space")
        await pilot.press(*letters)
        await pilot.press("enter")
        await pilot.pause()

    async def test_splash_then_area_list(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            self.assertIsInstance(self.app.screen, SplashScreen)
            await pilot.press("space")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, AreaListScreen)

    def app_with_splash_seconds(self, seconds: int) -> GoldED:
        config = UserConfig(splash_seconds=seconds)
        return GoldED(Session(open_message_store(self.path), config), "dark")

    async def test_splash_counts_down_from_config(self) -> None:
        app = self.app_with_splash_seconds(1)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            prompt = app.screen.query_one("#prompt", Static)
            self.assertTrue(str(prompt.content).endswith("wait  1"))
            await pilot.pause(1.5)
            self.assertIsInstance(app.screen, AreaListScreen)

    async def test_zero_splash_seconds_skips_splash(self) -> None:
        app = self.app_with_splash_seconds(0)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            self.assertIsInstance(app.screen, AreaListScreen)
            self.assertEqual(len(app.screen_stack), 2)

    async def test_brackets_in_area_names_are_text(self) -> None:
        path = f"{self.__tmp.name}/brackets.sqlite3"
        name = "[/b] Odd [reverse]name"
        store = create_message_store(path, (Area("[ECHO]", name),))
        store.append(
            "[ECHO]",
            OutgoingMessage(from_name="A", to_name="All", subject="s", body_text="b\n"),
        )
        app = GoldED(Session(open_message_store(path), UserConfig(splash_seconds=0)))
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            self.assertIsInstance(app.screen, MessageListScreen)
            title = app.screen.query_one("#title", Static).render()
            self.assertIn(f" {name} ", str(title))
            self.assertIn(" [ECHO] ", str(title))

    async def test_read_and_step_through_messages(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await self.open_area(pilot, "thr")
            self.assertIsInstance(self.app.screen, MessageListScreen)
            self.assertEqual(self.session.selected_area(), "THREADED")

            await pilot.press("enter")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, MessageViewScreen)
            self.assertEqual(self.session.current_message_index(), 0)

            await pilot.press("right")
            await pilot.pause()
            self.assertEqual(self.session.current_message_index(), 1)

            await pilot.press("left")
            await pilot.pause()
            self.assertEqual(self.session.current_message_index(), 0)

            await pilot.press("escape")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, MessageListScreen)
            await pilot.press("escape")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, AreaListScreen)

    async def test_pagebar_follows_list_scroll(self) -> None:
        store = open_message_store(self.path)
        for number in range(40):
            store.append(
                "THREADED",
                OutgoingMessage(
                    from_name="A", to_name="B", subject=f"s{number}", body_text="x"
                ),
            )

        async with self.app.run_test(size=(100, 15)) as pilot:
            await self.open_area(pilot, "thr")
            screen = self.app.screen
            assert isinstance(screen, MessageListScreen)
            pagebar = screen.query_one("#pagebar", Static)
            at_top = str(pagebar.content)

            # What the mouse wheel does: the viewport moves, the cursor stays.
            screen.table().scroll_to(y=30, animate=False)
            await pilot.pause()
            self.assertEqual(screen.table().cursor_row, 0)
            self.assertNotEqual(str(pagebar.content), at_top)

    async def test_toggle_theme(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await pilot.press("space", "f9")
            await pilot.pause()
            self.assertEqual(self.app.theme, "light")
            await pilot.press("f9")
            await pilot.pause()
            self.assertEqual(self.app.theme, "dark")

    async def test_write_and_save(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await self.open_area(pilot, "one")
            before = len(self.session.messages())

            await pilot.press("w")
            await pilot.pause()
            screen = self.app.screen
            self.assertIsInstance(screen, WriteMessageScreen)
            screen.query_one("#subject", Input).value = "Smoke test"
            screen.query_one(TextArea).text = "Written by the smoke test."

            await pilot.press("f2")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, MessageListScreen)
            messages = self.session.messages()
            self.assertEqual(len(messages), before + 1)
            self.assertEqual(messages[-1].subject, "Smoke test")
            self.assertEqual(messages[-1].from_name, "Tester")

    async def test_discard_draft(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await self.open_area(pilot, "one")
            before = len(self.session.messages())

            await pilot.press("w")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, DiscardDialog)

            await pilot.press("y")
            await pilot.pause()
            self.assertIsInstance(self.app.screen, MessageListScreen)
            self.assertIsNone(self.session.draft_message())
            self.assertEqual(len(self.session.messages()), before)

    async def test_q_quits_from_message_list(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await self.open_area(pilot, "one")
            await pilot.press("q")
            await pilot.pause()
            self.assertEqual(self.app.return_code, 0)

    async def test_q_filters_area_list_and_escape_quits(self) -> None:
        async with self.app.run_test(size=SIZE) as pilot:
            await pilot.press("space", "q")
            await pilot.pause()
            self.assertIsNone(self.app.return_code)
            self.assertIsInstance(self.app.screen, AreaListScreen)

            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(self.app.return_code, 0)
