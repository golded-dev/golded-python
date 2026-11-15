# GoldED.py

A message reader for FidoNet areas stored in SQLite. Terminal UI built with Textual. Storage comes from `golded-ftn` and `golded-ftn-sqlite`.

## Install

```bash
uv tool install golded
golded --help
```

Python 3.12 or newer. `golded` looks for `golded.toml` and `messages.sqlite3` in the current directory unless told otherwise (see Options).

## Layout

```
src/golded/cli.py   entry point (`golded`, `python -m golded`)
src/golded/ui/      draws the screen and handles keys (Textual)
src/golded/logic/   selected area, current message, navigation, draft
src/golded/data/    thin edge toward the FTN packages
scripts/            demo seeder (`seed_demo.py`) and release checks
tests/              unittest, run with pytest
```

`cli.py` opens the store and hands it to `ui/app.py`, which wraps it in a `logic` `Session`; the screens work through that session. The `golded-ftn` value types (`FtnAddress`, `OutgoingMessage`) are shared by all three layers.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python scripts/seed_demo.py
cp golded.toml.example golded.toml
uv run golded
uv run pytest
```

`scripts/seed_demo.py` writes `messages.sqlite3` (the same default as `golded`). **It deletes the file first if it exists, along with its `-wal` and `-shm` files**, so do not rerun it if you want to keep messages from a demo or manual test. `golded.toml` (copied from the example) points at that file and sets your From name and FTN address. Without a config the app still uses `messages.sqlite3`.

## Config (`golded.toml`)

TOML, read with the standard library's `tomllib`:

```toml
from_name = "Odinn"
from_address = "2:236/777"
database = "messages.sqlite3"
origin = "Where we're going, we don't need roads."
theme = "dark"
threaded_list = false
splash_seconds = 10
```

`from_name` and `from_address` are filled in automatically when you write or reply. `origin` becomes ` * Origin: …` below the tearline; the default is Doc Brown's "Where we're going, we don't need roads." `theme` is `dark` or `light` (default `dark`). `threaded_list` starts the message list as a thread tree (`true`) or flat (`false`, default); `t` still toggles it inside the app. `splash_seconds` is how long the splash screen counts down (default `10`); `0` skips it. An unknown `theme`, a `threaded_list` that is not a TOML boolean (`"no"` is a string), or a `splash_seconds` that is not a whole number of 0 or more stops `golded` at startup with an error. Product name and version are constants in the code. `--database` and `--theme` on the command line override the config.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--config PATH` | `golded.toml` | User config (TOML) |
| `--database PATH` | from config, else `messages.sqlite3` | SQLite message database |
| `--theme NAME` | from config, else `dark` | `dark` or `light` |

`light` is Black on LGrey with yellow rules and red titles. The theme can also be switched inside the app with `F9`.

## Keys

**Everywhere**

| Key | Action |
| --- | --- |
| `q` | Quit the app (message list and message view; in the area list letters filter, and in the write screen they are text) |
| `Esc` | Back one screen; quits from the area list |
| `F9` | Toggle theme |

**Splash**

| Key | Action |
| --- | --- |
| Any key | Continue to the area list (otherwise after the `splash_seconds` countdown, default 10) |

**Area list**

| Key | Action |
| --- | --- |
| `↑` `↓` | Move cursor |
| `Enter` | Open the area |
| `Space` / `Shift+Space` | Page down / up |
| Letters | Filter on area name or code (`Backspace` deletes) |

**Message list**

| Key | Action |
| --- | --- |
| `↑` `↓` | Move cursor |
| `Enter` | Open the message |
| `w` | Write a new message |
| `t` | Toggle between flat list and thread tree (`reply_to_msgno`) |
| `Esc` | Back to the area list |
| `Space` / `Shift+Space` | Page down / up |

**Message view**

| Key | Action |
| --- | --- |
| `Esc` | Back to the message list |
| `→` | Next message |
| `←` | Previous message |
| `Shift+→` / `Shift+←` | Next / previous in the same subject thread |
| `Space` / `Shift+Space` | Page down / up in the body |
| `m` | Mojibake repair on/off (display only; the database is not changed) |
| `w` | Write a new message |
| `r` | Reply (quotes the displayed body and subject, with the repair applied if `m` is on) |

**Write / reply**

| Key | Action |
| --- | --- |
| `Cmd+S` / `Ctrl+S` / `F2` | Save message |
| `↑` / `↓` | Move focus between From / To / Subj / body (in the body, `↑` on the top line goes to Subj) |
| `Esc` | Cancel (asks before discarding the draft) |

The header mirrors the reading screen: Msg line, From (name, address, date), To (name and address), Subj and a separator above the body. A new echomail message sets To to `All`. In netmail the recipient's FTN address goes in the To address field (required to save). A reply starts with `Hello {first name}` and a blank line before the quote (FL initials: `Alice Bob` → `AB>`). Quotes stop at the tearline (`---`).

## License

MIT. See [LICENSE](LICENSE).
