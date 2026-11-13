import argparse
import sqlite3
import sys

from logic.user_config import THEME_NAMES, load_user_config
from ui.app import run

DEFAULT_DATABASE = "messages.sqlite3"
DEFAULT_CONFIG = "golded.toml"

def main() -> None:
    parser = argparse.ArgumentParser(description = "GoldED.py message reader")
    parser.add_argument(
        "--config",
        default = DEFAULT_CONFIG,
        help = "path to golded.toml (default: golded.toml)",
    )
    parser.add_argument(
        "--database",
        default = None,
        help = "path to SQLite message database (overrides config)",
    )
    parser.add_argument(
        "--theme",
        choices = THEME_NAMES,
        default = None,
        help = "colour theme (overrides config; toggle with F9)",
    )
    args = parser.parse_args()

    user_config = load_user_config(args.config)

    if args.database is None:
        database = DEFAULT_DATABASE if user_config.database == "" else user_config.database
    else:
        database = args.database

    theme = user_config.theme if args.theme is None else args.theme

    try:
        run(database, theme, user_config)
    except FileNotFoundError:
        print(f"Database not found: {database}", file = sys.stderr)
        print("Create one with: python seed.py", file = sys.stderr)
        raise SystemExit(1)
    except sqlite3.Error as error:
        print(f"Cannot open database {database}: {error}", file = sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
