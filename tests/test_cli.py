"""Startup errors end with a short message and exit code 1, not a traceback."""

import gc
import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from golded import cli


class CliErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.__tmp.name)

    def tearDown(self) -> None:
        self.__tmp.cleanup()

    def fail_with(self, *args: str) -> str:
        stderr = io.StringIO()
        argv = ["golded", "--config", str(self.dir / "absent.toml"), *args]
        with (
            mock.patch("sys.argv", argv),
            mock.patch.object(cli, "run") as run,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            cli.main()
        self.assertEqual(raised.exception.code, 1)
        run.assert_not_called()
        self.assertNotIn("Traceback", stderr.getvalue())
        # golded-ftn-sqlite leaves its connection open when the file is not SQLite,
        # and the traceback behind SystemExit keeps it alive. Windows cannot delete
        # an open file, so release it before tearDown removes the directory.
        del raised
        gc.collect()
        return stderr.getvalue()

    def test_missing_database(self) -> None:
        output = self.fail_with("--database", str(self.dir / "absent.sqlite3"))
        self.assertIn("Database not found", output)

    def test_not_a_database(self) -> None:
        path = self.dir / "text.sqlite3"
        path.write_text("hello\n")
        output = self.fail_with("--database", str(path))
        self.assertIn("Cannot open database", output)

    def test_foreign_schema(self) -> None:
        path = self.dir / "other.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.execute("create table t (x)")
        connection.close()
        output = self.fail_with("--database", str(path))
        self.assertIn("not a supported golded-ftn-sqlite database", output)

    def test_malformed_config(self) -> None:
        config = self.dir / "golded.toml"
        config.write_text('from_name = "unterminated\n')
        output = self.fail_with("--config", str(config))
        self.assertIn("Cannot read config", output)

    def test_invalid_from_address(self) -> None:
        config = self.dir / "golded.toml"
        config.write_text('from_address = "nonsense"\n')
        output = self.fail_with("--config", str(config))
        self.assertIn("Invalid FTN address [nonsense]", output)
