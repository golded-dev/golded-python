# golded

A terminal message reader for FidoNet echomail and netmail stored in SQLite or JAM, modelled on GoldED. Built with Textual. Storage uses [`golded-ftn-sqlite`](https://pypi.org/project/golded-ftn-sqlite/) and [`golded-ftn-jam`](https://pypi.org/project/golded-ftn-jam/).

The manual covers message bases, configuration, every key and each screen: <https://golded-dev.github.io/golded-python/>. Its source is in `site/`, built by `scripts/build_pages.py`.

## Install

```bash
uv tool install golded
golded --help
```

Python 3.12 or newer, on Linux, macOS or Windows. `pipx install golded` works too.

## Run

```bash
golded --database messages.sqlite3
```

`golded --database` opens one golded-ftn-sqlite base. Without options it looks for `messages.sqlite3` and `golded.toml` in the current directory. The manual shows how to create a base with `ftnt` from [`golded-ftn-tools`](https://pypi.org/project/golded-ftn-tools/).

`↑` `↓` and `Enter` pick an area and a message, `←` `→` step through messages, `r` replies, `F2` saves, `Esc` goes back and quits from the area list.

## Config

`golded.toml` sets who you are when you write:

```toml
from_name = "Odinn"
from_address = "2:236/777"
database = "messages.sqlite3"
origin = "Where we're going, we don't need roads."
theme = "dark"
threaded_list = false
splash_seconds = 10
```

`--config`, `--database` and `--theme` override the file. A value golded cannot use stops it at startup with one line and exit status 1. The manual describes each field.

For JAM bases or areas spread across several bases, use `golded --area-config golded.cfg`:

```text
AREADEF GENERAL "General discussion" A Echo SQLite "bases/echo.sqlite3" . ()
AREADEF NETMAIL "Private mail" 0 Net SQLite bases/mail.sqlite3 . ()
AREADEF UNIX "UNIX discussion" A Echo JAM bases/UNIX . ()
```

For SQLite, the echo ID and type must match an area in the named database. For JAM, specify the base filename without its extension. Relative paths start at the configuration file. The configuration page in the manual describes the supported subset of classic `AREADEF` syntax.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python scripts/seed_demo.py
cp golded.toml.example golded.toml
uv run golded
```

`scripts/seed_demo.py` writes a demo `messages.sqlite3`. **It deletes that file first if it exists, along with its `-wal` and `-shm` files.**

```
src/golded/cli.py   entry point (`golded`, `python -m golded`)
src/golded/ui/      draws the screen and handles keys (Textual)
src/golded/logic/   selected area, current message, navigation, draft
src/golded/data/    thin edge toward the FTN packages
scripts/            demo seeder, manual builder and release checks
tests/              unittest, run with pytest
```

`cli.py` opens the store and hands it to `ui/app.py`, which wraps it in a `logic` `Session`; the screens work through that session.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the checks and [docs/release.md](docs/release.md) for release preparation.

## License

MIT. See [LICENSE](LICENSE).
