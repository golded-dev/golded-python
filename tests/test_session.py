import tempfile
import unittest

from golded_ftn import FtnAddress, OutgoingMessage, ParsedMessage

from golded.data.store import open_message_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig
from golded.logic.version import PRODUCT
from seed_demo import seed_database


class SessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        path = f"{self.__tmp.name}/test.sqlite3"
        seed_database(path)
        store = open_message_store(path)
        self.session = Session(store)

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def current(self) -> ParsedMessage:
        message = self.session.current_message()
        assert message is not None
        return message

    def draft(self) -> OutgoingMessage:
        message = self.session.draft_message()
        assert message is not None
        return message

    def test_empty_area(self) -> None:
        self.session.select_area("EMPTY")
        self.assertEqual(self.session.messages(), ())
        self.assertIsNone(self.session.current_message())

    def test_one_message(self) -> None:
        self.session.select_area("ONE")
        messages = self.session.messages()
        self.assertEqual(len(messages), 1)

        self.session.select_message(messages[0].msgno)
        self.assertEqual(self.current().msgno, messages[0].msgno)

    def test_holes_next_previous(self) -> None:
        self.session.select_area("HOLE")
        messages = self.session.messages()
        self.assertEqual(len(messages), 3)

        first = messages[0].msgno
        middle = messages[1].msgno
        last = messages[2].msgno

        self.assertEqual([first, middle, last], [1, 2, 4])

        self.session.select_message(first)

        self.session.next_message()
        self.assertEqual(self.current().msgno, middle)

        self.session.next_message()
        self.assertEqual(self.current().msgno, last)

        # Can't go next of last message.
        self.session.next_message()
        self.assertEqual(self.current().msgno, last)

        self.session.previous_message()
        self.assertEqual(self.current().msgno, middle)

        self.session.previous_message()
        self.assertEqual(self.current().msgno, first)

        # Can't go previous of first message.
        self.session.previous_message()
        self.assertEqual(self.current().msgno, first)

    def test_next_previous_by_subject(self) -> None:
        self.session.select_area("THREADED")
        messages = self.session.messages()
        self.assertEqual(len(messages), 5)

        self.session.select_message(messages[0].msgno)

        self.session.next_message()
        self.assertEqual(self.current().from_name, "Mark Marksen")

        self.session.select_message(messages[0].msgno)
        self.session.next_subject_message()
        self.assertEqual(self.current().from_name, "Bob")

        self.session.next_subject_message()
        self.assertEqual(self.current().from_name, "Clara")

        self.session.next_subject_message()
        self.assertEqual(self.current().from_name, "Diana")

        self.session.next_subject_message()
        self.assertEqual(self.current().from_name, "Diana")

        self.session.previous_subject_message()
        self.assertEqual(self.current().from_name, "Clara")

        self.session.previous_subject_message()
        self.assertEqual(self.current().from_name, "Bob")

        self.session.previous_subject_message()
        self.assertEqual(self.current().from_name, "Alice")

        self.session.previous_subject_message()
        self.assertEqual(self.current().from_name, "Alice")

    def test_threaded_list_default_from_config(self) -> None:
        store = open_message_store(f"{self.__tmp.name}/test.sqlite3")
        session = Session(store, UserConfig(threaded_list=True))
        self.assertTrue(session.threaded_list())
        session.select_area("THREADED")
        names = [m.from_name for m in session.messages()]
        self.assertEqual(
            names,
            ["Alice", "Bob", "Diana", "Clara", "Mark Marksen"],
        )

    def test_toggle_threaded_list_reorders_and_keeps_message(self) -> None:
        self.session.select_area("THREADED")
        flat = [m.from_name for m in self.session.messages()]
        self.assertEqual(
            flat,
            ["Alice", "Mark Marksen", "Bob", "Clara", "Diana"],
        )
        self.assertFalse(self.session.threaded_list())

        self.session.select_message(self.session.messages()[3].msgno)
        self.assertEqual(self.current().from_name, "Clara")

        self.session.toggle_threaded_list()
        self.assertTrue(self.session.threaded_list())
        threaded = [m.from_name for m in self.session.messages()]
        self.assertEqual(
            threaded,
            ["Alice", "Bob", "Diana", "Clara", "Mark Marksen"],
        )
        self.assertEqual(self.current().from_name, "Clara")

        rows = self.session.message_rows()
        self.assertEqual(rows[1].branch_path, [True])
        self.assertEqual(rows[2].branch_path, [True, False])
        self.assertEqual(rows[3].branch_path, [False])

        self.session.toggle_threaded_list()
        self.assertFalse(self.session.threaded_list())
        self.assertEqual(
            [m.from_name for m in self.session.messages()],
            ["Alice", "Mark Marksen", "Bob", "Clara", "Diana"],
        )
        self.assertEqual(self.current().from_name, "Clara")

    def test_area_switch_clears_message(self) -> None:
        self.session.select_area("ONE")
        messages = self.session.messages()
        self.session.select_message(messages[0].msgno)
        self.assertIsNotNone(self.session.current_message())

        self.session.select_area("EMPTY")
        self.assertIsNone(self.session.current_message())
        self.assertEqual(self.session.messages(), ())

    def test_draft_keeps_area(self) -> None:
        self.session.select_area("ONE")
        self.session.start_draft_message()
        self.assertEqual(self.session.draft_area(), "ONE")
        self.assertIsNotNone(self.session.draft_message())

        self.session.select_area("EMPTY")
        self.assertEqual(self.session.draft_area(), "ONE")
        self.assertIsNotNone(self.session.draft_message())

    def test_save_draft(self) -> None:
        self.session.select_area("ONE")
        self.session.start_draft_message()
        draft_message = OutgoingMessage(
            from_name="Odinn",
            to_name="All",
            subject="Draft save",
            body_text="Hello",
        )
        self.session.set_draft_message(draft_message)

        msgno = self.session.save_draft_message()
        assert msgno is not None

        self.assertEqual(msgno, 2)
        self.assertIsNone(self.session.draft_message())
        self.assertIsNone(self.session.draft_area())

        self.session.select_area("ONE")
        messages = self.session.messages()
        self.assertEqual(len(messages), 2)

        self.session.select_message(msgno)
        current = self.current()
        self.assertEqual(current.from_name, "Odinn")
        self.assertEqual(current.to_name, "All")
        self.assertEqual(current.subject, "Draft save")
        self.assertIn("Hello", current.body_text)
        self.assertIn(f"--- {PRODUCT}", current.body_text)
        self.assertIn(
            " * Origin: Where we're going, we don't need roads.", current.body_text
        )

    def test_save_draft_rejects_empty_fields(self) -> None:
        self.session.select_area("ONE")
        self.session.start_draft_message()

        with self.assertRaises(ValueError):
            self.session.save_draft_message()

        self.assertIsNotNone(self.session.draft_message())
        self.assertEqual(self.session.draft_area(), "ONE")

    def test_discard_draft(self) -> None:
        self.session.select_area("ONE")
        self.session.start_draft_message()
        self.session.discard_draft_message()
        self.assertIsNone(self.session.draft_message())
        self.assertIsNone(self.session.draft_area())

    def test_start_reply_draft(self) -> None:
        self.session.select_area("THREADED")
        messages = self.session.messages()
        self.session.select_message(messages[0].msgno)

        quoted = "Hello Alice\n---- skillelinje\nEfter\n\n--- Old\n * Origin: old"
        self.session.start_reply_draft(quoted)
        draft = self.draft()

        self.assertEqual(self.session.draft_area(), "THREADED")
        self.assertEqual(draft.to_name, "Alice")
        self.assertEqual(str(draft.to_address), messages[0].from_address)
        self.assertEqual(draft.subject, "Re: First message")
        self.assertEqual(draft.reply_to_msgno, messages[0].msgno)
        self.assertEqual(draft.from_name, "")
        self.assertTrue(draft.body_text.startswith("Hello Alice\n\nA> Hello Alice\n"))
        self.assertIn("A> ---- skillelinje", draft.body_text)
        self.assertIn("A> Efter", draft.body_text)
        self.assertIn(f"--- {PRODUCT}", draft.body_text)
        self.assertIn(
            " * Origin: Where we're going, we don't need roads.", draft.body_text
        )
        self.assertNotIn("Old", draft.body_text)
        self.assertNotIn(" * Origin: old", draft.body_text)

    def test_start_draft_echomail_to_all(self) -> None:
        self.session.select_area("ONE")
        self.session.start_draft_message()
        self.assertEqual(self.draft().to_name, "All")

    def test_start_draft_netmail_to_empty(self) -> None:
        self.session.select_area("NETMAIL")
        self.session.start_draft_message()
        self.assertEqual(self.draft().to_name, "")

    def test_start_reply_draft_without_message(self) -> None:
        self.session.select_area("EMPTY")
        self.session.start_reply_draft("ignored")
        self.assertIsNone(self.session.draft_message())

    def test_start_reply_draft_uses_given_body(self) -> None:
        self.session.select_area("THREADED")
        messages = self.session.messages()
        self.session.select_message(messages[0].msgno)

        self.session.start_reply_draft("svære med bonsai")
        draft = self.draft()
        self.assertIn("svære med bonsai", draft.body_text)

    def test_start_reply_draft_uses_given_subject(self) -> None:
        self.session.select_area("THREADED")
        messages = self.session.messages()
        self.session.select_message(messages[0].msgno)

        self.session.start_reply_draft("hi", "Møjdyr")
        draft = self.draft()
        self.assertEqual(draft.subject, "Re: Møjdyr")

    def test_draft_uses_user_config(self) -> None:
        address = FtnAddress.from_string("2:236/777")
        store = open_message_store(f"{self.__tmp.name}/test.sqlite3")
        session = Session(
            store,
            UserConfig(from_name="Odinn", from_address=address),
        )
        session.select_area("ONE")
        session.start_draft_message()
        draft = session.draft_message()
        assert draft is not None
        self.assertEqual(draft.from_name, "Odinn")
        self.assertEqual(draft.from_address, address)

        original = session.messages()[0]
        session.select_message(original.msgno)
        session.start_reply_draft("hi")
        reply = session.draft_message()
        assert reply is not None
        self.assertEqual(reply.from_name, "Odinn")
        self.assertEqual(reply.from_address, address)
        self.assertEqual(str(reply.to_address), original.from_address)

    def test_failed_save_keeps_draft(self) -> None:
        self.session.select_area("NETMAIL")
        self.session.start_draft_message()
        self.session.set_draft_message(
            OutgoingMessage(
                from_name="Odinn",
                to_name="Alice",
                subject="Netmail try",
                body_text="Hello",
            )
        )

        with self.assertRaises(ValueError) as error:
            self.session.save_draft_message()

        self.assertIn("destination address", str(error.exception))
        self.assertIsNotNone(self.session.draft_message())
        self.assertEqual(self.session.draft_area(), "NETMAIL")

    def test_save_netmail_with_destination(self) -> None:
        address = FtnAddress.from_string("2:5020/1234")
        self.session.select_area("NETMAIL")
        self.session.start_draft_message()
        self.session.set_draft_message(
            OutgoingMessage(
                from_name="Odinn",
                to_name="Alice",
                subject="Netmail try",
                body_text="Hello",
                from_address=FtnAddress.from_string("2:236/777"),
                to_address=address,
            )
        )

        msgno = self.session.save_draft_message()
        self.assertIsNotNone(msgno)
        saved = self.session.messages()[-1]
        self.assertEqual(str(saved.to_address), str(address))

    def test_area_name(self) -> None:
        self.assertEqual(self.session.area_name("ONE"), "Area with one message")
        self.assertEqual(self.session.area_name("MISSING"), "MISSING")


if __name__ == "__main__":
    unittest.main()
