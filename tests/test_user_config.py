import tempfile
import unittest
from pathlib import Path

from golded_ftn import FtnAddress

from logic.tear_origin import DEFAULT_ORIGIN
from logic.user_config import (
    DEFAULT_THEME,
    DEFAULT_THREADED_LIST,
    load_user_config,
)

class UserConfigTests(unittest.TestCase):
    def test_missing_file_is_empty(self):
        config = load_user_config("/tmp/does-not-exist-golded.toml")
        self.assertEqual(config.from_name, "")
        self.assertIsNone(config.from_address)
        self.assertEqual(config.database, "")
        self.assertEqual(config.origin, DEFAULT_ORIGIN)
        self.assertEqual(config.theme, DEFAULT_THEME)
        self.assertEqual(config.threaded_list, DEFAULT_THREADED_LIST)

    def test_loads_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "golded.toml"
            path.write_text(
                'from_name = "Odinn"\n'
                'from_address = "2:236/777"\n'
                'database = "messages.sqlite3"\n'
                'origin = "Coffee and packets"\n'
                'theme = "light"\n'
                "threaded_list = true\n",
                encoding = "utf-8",
            )
            config = load_user_config(path)

        self.assertEqual(config.from_name, "Odinn")
        self.assertEqual(config.from_address, FtnAddress.from_string("2:236/777"))
        self.assertEqual(config.database, "messages.sqlite3")
        self.assertEqual(config.origin, "Coffee and packets")
        self.assertEqual(config.theme, "light")
        self.assertTrue(config.threaded_list)

    def test_unknown_theme_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "golded.toml"
            path.write_text('theme = "neon"\n', encoding = "utf-8")
            config = load_user_config(path)

        self.assertEqual(config.theme, DEFAULT_THEME)

if __name__ == "__main__":
    unittest.main()
