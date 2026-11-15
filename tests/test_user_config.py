import tempfile
import unittest
from pathlib import Path

from golded_ftn import FtnAddress

from golded.logic.tear_origin import DEFAULT_ORIGIN
from golded.logic.user_config import (
    DEFAULT_SPLASH_SECONDS,
    DEFAULT_THEME,
    DEFAULT_THREADED_LIST,
    load_user_config,
)


class UserConfigTests(unittest.TestCase):
    def test_missing_file_is_empty(self) -> None:
        config = load_user_config("/tmp/does-not-exist-golded.toml")
        self.assertEqual(config.from_name, "")
        self.assertIsNone(config.from_address)
        self.assertEqual(config.database, "")
        self.assertEqual(config.origin, DEFAULT_ORIGIN)
        self.assertEqual(config.theme, DEFAULT_THEME)
        self.assertEqual(config.threaded_list, DEFAULT_THREADED_LIST)
        self.assertEqual(config.splash_seconds, DEFAULT_SPLASH_SECONDS)

    def test_loads_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "golded.toml"
            path.write_text(
                'from_name = "Odinn"\n'
                'from_address = "2:236/777"\n'
                'database = "messages.sqlite3"\n'
                'origin = "Coffee and packets"\n'
                'theme = "light"\n'
                "threaded_list = true\n"
                "splash_seconds = 0\n",
                encoding="utf-8",
            )
            config = load_user_config(path)

        self.assertEqual(config.from_name, "Odinn")
        self.assertEqual(config.from_address, FtnAddress.from_string("2:236/777"))
        self.assertEqual(config.database, "messages.sqlite3")
        self.assertEqual(config.origin, "Coffee and packets")
        self.assertEqual(config.theme, "light")
        self.assertTrue(config.threaded_list)
        self.assertEqual(config.splash_seconds, 0)

    def load_text(self, text: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "golded.toml"
            path.write_text(text, encoding="utf-8")
            load_user_config(path)

    def test_unknown_theme_is_an_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "theme must be one of dark, light"):
            self.load_text('theme = "neon"\n')

    def test_threaded_list_must_be_boolean(self) -> None:
        with self.assertRaisesRegex(ValueError, "threaded_list must be true or false"):
            self.load_text('threaded_list = "no"\n')

    def test_splash_seconds_must_be_a_whole_number(self) -> None:
        for value in ("-1", "2.5", '"10"', "true"):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "splash_seconds must be"),
            ):
                self.load_text(f"splash_seconds = {value}\n")


if __name__ == "__main__":
    unittest.main()
