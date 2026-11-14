"""Append a message and read it back."""

import tempfile
import unittest
from pathlib import Path

from golded_ftn import OutgoingMessage

from golded.data.area import Area
from golded.data.store import create_message_store, open_message_store


class MessageStoreTests(unittest.TestCase):
    def test_append_and_reread(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.sqlite3"
            store = create_message_store(
                path,
                areas=(
                    Area("EMPTY", "Empty"),
                    Area("MAIL", "Mail"),
                ),
            )

            areas = store.areas()
            codes = []
            for area in areas:
                codes.append(area.code)
            self.assertEqual(codes, ["EMPTY", "MAIL"])
            self.assertEqual(store.messages("EMPTY"), ())

            msgno = store.append(
                "MAIL",
                OutgoingMessage(
                    from_name="Odinn",
                    to_name="All",
                    subject="Layer check",
                    body_text="Stored through MessageStore.",
                ),
            )
            self.assertEqual(msgno, 1)

            again = open_message_store(path)
            messages = again.messages("MAIL")
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].msgno, 1)
            self.assertEqual(messages[0].subject, "Layer check")

            one = again.message("MAIL", 1)
            self.assertEqual(one.body_text, "Stored through MessageStore.")


if __name__ == "__main__":
    unittest.main()
