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

    def test_bad_areadef(self) -> None:
        config = self.dir / "golded.cfg"
        config.write_text('AREADEF MAIL "Mail" A Echo Hudson 10 . ()\n')
        output = self.fail_with("--area-config", str(config))
        self.assertIn(f"{config}:1: unsupported message-base format Hudson", output)

    def test_area_config_opens_configured_areas_with_toml_preferences(self) -> None:
        from golded.data.area import Area
        from golded.data.store import create_message_store

        create_message_store(
            self.dir / "mail.sqlite3", [Area("MAIL", "Mail", "netmail")]
        )
        config = self.dir / "golded.cfg"
        config.write_text(
            'AREADEF mail "Private mail" 0 Net SQLite mail.sqlite3 . ()\n'
        )
        preferences = self.dir / "golded.toml"
        preferences.write_text(
            'database = "absent.sqlite3"\nfrom_name = "Alice"\nareas = "ignored"\n'
        )
        argv = [
            "golded",
            "--config",
            str(preferences),
            "--area-config",
            str(config),
            "--theme",
            "light",
        ]

        with mock.patch("sys.argv", argv), mock.patch.object(cli, "run") as run:
            cli.main()

        run.assert_called_once()
        store, theme, user_config = run.call_args.args
        self.assertEqual(
            [(area.code, area.name, area.kind) for area in store.areas()],
            [("mail", "Private mail", "netmail")],
        )
        self.assertEqual(store.messages("mail"), ())
        self.assertEqual(theme, "light")
        self.assertEqual(user_config.from_name, "Alice")

    def test_missing_jam_files(self) -> None:
        config = self.dir / "golded.cfg"
        config.write_text('AREADEF MAIL "Mail" 0 Net JAM missing . ()\n')
        output = self.fail_with("--area-config", str(config))
        self.assertIn(f"{config}:1: cannot open JAM base", output)
        self.assertIn("Missing JAM file", output)

    def test_toml_areas_route_in_declaration_order(self) -> None:
        from golded.data.area import Area
        from golded.data.store import create_message_store

        create_message_store(
            self.dir / "mail.sqlite3",
            [
                Area("LOCAL", "Local", "netmail"),
                Area("FIDONET.GENERAL", "General", "echomail"),
            ],
        )
        config = self.dir / "golded.toml"
        config.write_text(
            'database = "absent.sqlite3"\n'
            "[areas]\n"
            '"FIDONET.GENERAL" = { description = "General discussion", group = "A", '
            'type = "echo", format = "sqlite", path = "mail.sqlite3" }\n'
            'LOCAL = { description = "Local mail", group = "0", '
            'type = "net", format = "sqlite", path = "mail.sqlite3" }\n'
        )
        with (
            mock.patch("sys.argv", ["golded", "--config", str(config)]),
            mock.patch.object(cli, "run") as run,
        ):
            cli.main()

        store, _, _ = run.call_args.args
        self.assertEqual(
            [(area.code, area.name, area.kind) for area in store.areas()],
            [
                ("FIDONET.GENERAL", "General discussion", "echomail"),
                ("LOCAL", "Local mail", "netmail"),
            ],
        )
        self.assertEqual(store.messages("FIDONET.GENERAL"), ())

    def test_explicit_database_uses_preferences_and_skips_toml_areas(self) -> None:
        from golded.data.area import Area
        from golded.data.store import create_message_store

        database = self.dir / "mail.sqlite3"
        create_message_store(database, [Area("MAIL", "Mail", "netmail")])
        config = self.dir / "golded.toml"
        config.write_text(
            'from_name = "Alice"\nareas = "ignored"\n[jam]\nread_mode = false\n'
        )
        with (
            mock.patch(
                "sys.argv",
                ["golded", "--config", str(config), "--database", str(database)],
            ),
            mock.patch.object(cli, "run") as run,
        ):
            cli.main()

        store, _, user_config = run.call_args.args
        self.assertEqual([area.code for area in store.areas()], ["MAIL"])
        self.assertEqual(user_config.from_name, "Alice")

    def test_invalid_toml_read_modes(self) -> None:
        config = self.dir / "golded.toml"
        entry = (
            'MAIL = { description = "Mail", group = "A", type = "net", path = "mail"'
        )
        for content, error in (
            ('[jam]\nread_mode = "loose"\n', "jam.read_mode must be strict or lenient"),
            (
                "[areas]\n" + entry + ', format = "jam", read_mode = false }\n',
                "areas['MAIL'].read_mode must be strict or lenient",
            ),
            (
                "[areas]\n" + entry + ', format = "sqlite", read_mode = "strict" }\n',
                "areas['MAIL'].read_mode is only valid for JAM areas",
            ),
        ):
            with self.subTest(content=content):
                config.write_text(content)
                self.assertIn(error, self.fail_with("--config", str(config)))
