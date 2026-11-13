# GoldED.py

A message reader for FidoNet areas stored in SQLite. Terminal UI built with Textual. Storage comes from `golded-ftn` and `golded-ftn-sqlite`.

## Layout

```
app.py      entry point
ui/         draws the screen and handles keys (Textual)
logic/      selected area, current message, navigation, draft
data/       thin edge toward the FTN packages
seed.py     builds a reproducible test database
tests/      unittest
```

`ui/app.py` opens the store and hands it to a `logic` `Session`; the screens work through that session. The `golded-ftn` value types (`FtnAddress`, `OutgoingMessage`) are shared by all three layers.

## Environment

Requires [uv](https://docs.astral.sh/uv/). uv fetches Python 3.14 itself if it is missing.

```bash
uv venv --python 3.14
uv pip install -r requirements.txt
```

`requirements.txt` pins Textual 8.2.8, `golded-ftn` 1.5.1 and `golded-ftn-sqlite` 1.1.0.

## Run

```bash
uv run python seed.py
cp golded.toml.example golded.toml
uv run python app.py
uv run python -m unittest discover -s tests
```

`seed.py` writes `messages.sqlite3` (the same default as `app.py`). **It deletes the file first if it exists, along with its `-wal` and `-shm` files**, so do not rerun it if you want to keep messages from a demo or manual test. Use `seed.py` for reproducible test data and `unittest`; for everyday use `uv run python app.py` is enough. `golded.toml` (copied from the example) points at that file and sets your From name and FTN address. Without a config the app still uses `messages.sqlite3`.

## Config (`golded.toml`)

TOML, read with the standard library's `tomllib`:

```toml
from_name = "Odinn"
from_address = "2:236/777"
database = "messages.sqlite3"
origin = "Where we're going, we don't need roads."
theme = "dark"
threaded_list = false
```

`from_name` and `from_address` are filled in automatically when you write or reply. `origin` becomes ` * Origin: …` below the tearline; the default is Doc Brown's "Where we're going, we don't need roads." `theme` is `dark` or `light` (default `dark`). `threaded_list` starts the message list as a thread tree (`true`) or flat (`false`, default); `t` still toggles it inside the app. Product name and version are constants in the code. `--database` and `--theme` on the command line override the config.

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
| `q` | Quit the app |
| `Esc` | Back one screen; quits from the area list |
| `F9` | Toggle theme |

**Splash**

| Key | Action |
| --- | --- |
| Any key | Continue to the area list (otherwise after a 10–1 countdown) |

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
