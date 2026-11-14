import argparse
import sqlite3
import sys

from golded.data.store import open_message_store
from golded.logic.user_config import THEME_NAMES, load_user_config
from golded.ui.app import run

DEFAULT_DATABASE = "messages.sqlite3"
DEFAULT_CONFIG = "golded.toml"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="golded", description="GoldED.py message reader"
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help="path to golded.toml (default: golded.toml)",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="path to SQLite message database (overrides config)",
    )
    parser.add_argument(
        "--theme",
        choices=THEME_NAMES,
        default=None,
        help="colour theme (overrides config; toggle with F9)",
    )
    args = parser.parse_args()

    try:
        user_config = load_user_config(args.config)
    except (OSError, ValueError) as error:
        print(f"Cannot read config {args.config}: {error}", file=sys.stderr)
        raise SystemExit(1) from None

    if args.database is None:
        database = (
            DEFAULT_DATABASE if user_config.database == "" else user_config.database
        )
    else:
        database = args.database

    theme = user_config.theme if args.theme is None else args.theme

    try:
        store = open_message_store(database)
    except FileNotFoundError:
        print(f"Database not found: {database}", file=sys.stderr)
        print("Pass --database PATH or set database in golded.toml.", file=sys.stderr)
        raise SystemExit(1) from None
    except (sqlite3.Error, ValueError) as error:
        # golded-ftn-sqlite raises ValueError for a foreign or unsupported schema.
        print(f"Cannot open database {database}: {error}", file=sys.stderr)
        raise SystemExit(1) from None

    run(store, theme, user_config)


if __name__ == "__main__":
    main()
