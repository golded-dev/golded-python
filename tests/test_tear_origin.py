import unittest

from golded_ftn import FtnAddress

from golded.logic.tear_origin import DEFAULT_ORIGIN, tear_origin_block, with_tear_origin
from golded.logic.version import PRODUCT


class TearOriginTests(unittest.TestCase):
    def test_block_with_address(self):
        address = FtnAddress.from_string("2:236/777")
        text = tear_origin_block("Where we're going, we don't need roads.", address)
        self.assertEqual(
            text,
            f"--- {PRODUCT}\n"
            " * Origin: Where we're going, we don't need roads. (2:236/777)\n",
        )

    def test_block_without_address(self):
        text = tear_origin_block("Hello")
        self.assertEqual(text, f"--- {PRODUCT}\n * Origin: Hello\n")

    def test_empty_origin_uses_default(self):
        text = tear_origin_block("")
        self.assertIn(DEFAULT_ORIGIN, text)

    def test_with_tear_origin_appends(self):
        result = with_tear_origin("Hello", "Where we're going, we don't need roads.")
        self.assertTrue(result.startswith("Hello\n\n--- "))
        self.assertIn(" * Origin: Where we're going, we don't need roads.\n", result)

    def test_with_tear_origin_replaces_old_footer(self):
        body = "Hello\n--- Old\n * Origin: x"
        result = with_tear_origin(body, "Where we're going, we don't need roads.")
        self.assertNotIn("Old", result)
        self.assertIn("Where we're going, we don't need roads.", result)
        self.assertTrue(result.startswith("Hello\n\n--- "))

    def test_with_tear_origin_keeps_user_dash_line(self):
        body = "Før\n---- skillelinje\nEfter"
        result = with_tear_origin(body, "Where we're going, we don't need roads.")
        self.assertIn("---- skillelinje", result)
        self.assertIn("Efter", result)
        self.assertIn("Where we're going, we don't need roads.", result)


if __name__ == "__main__":
    unittest.main()
