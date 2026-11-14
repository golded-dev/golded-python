"""Drive the Textual app headless against a seeded database."""

import tempfile
import unittest

from golded_ftn import FtnAddress
from textual.pilot import Pilot
from textual.widgets import Input, TextArea

from golded.data.store import open_message_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig
from golded.ui.app import GoldED
from golded.ui.area_list import AreaListScreen
from golded.ui.message_list import MessageListScreen
from golded.ui.message_view import MessageViewScreen
from golded.ui.splash import SplashScreen
from golded.ui.write_message import DiscardDialog, WriteMessageScreen
from seed import seed_database

SIZE = (100, 30)


class AppSmokeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        path = f"{self.__tmp.name}/test.sqlite3"
        seed_database(path)
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
