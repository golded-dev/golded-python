# Verification: golded 1.0.0

Results of the Phase 4 review pass (see `docs/PLAN.md`). Automated checks are
repeatable; the manual terminal checks are filled in by whoever runs them.

## Course leftovers (2026-11-14)

`grep -rniE "kursist|itucation|eksamen|lasse|undervis|aflevering|conda"` over the
tree without `.venv`, `.git` and `uv.lock`: hits only in `docs/PLAN.md` (history and
the plan itself) and `classes=` in `ui/write_message.py` (substring of "lasse").

`grep -rnE "[æøåÆØÅ]"` over `src`, `seed.py`, `scripts`, `tests`, README and the
example config: hits only in test fixtures (`test_quote.py`, `test_display_text.py`,
`test_tear_origin.py`, `test_session.py`), where Danish text is the data under test
(mojibake repair, tearline handling). A word search for common Danish words in
`src`, `seed.py` and `scripts` finds only `RELEASE_NAME = "Stille og roligt™
edition"`, which is decision D7.

## Startup error paths (2026-11-14)

Probed with the installed `golded` command, stdin from `/dev/null`, 6 s timeout.
Covered by `tests/test_cli.py` except where noted.

| Case | Before | Now |
| --- | --- | --- |
| Database path does not exist | `Database not found` + hint, exit 1 | unchanged |
| Database path is a directory | `Database not found` + hint, exit 1 | unchanged (not a test) |
| File is not SQLite | `Cannot open database …: file is not a database`, exit 1 | unchanged |
| SQLite file with another schema, or a newer/older golded-ftn-sqlite schema | traceback (`ValueError`), exit 1 | `Cannot open database …: not a supported golded-ftn-sqlite database`, exit 1 |
| Empty file | traceback, exit 1 | same one-line message as above (not a test) |
| Directory not writable (WAL needs `-shm`) | `Cannot open database …: attempt to write a readonly database`, exit 1 | unchanged (not a test) |
| Database file read-only (`chmod 444`) | app starts and reads; saving shows `attempt to write a readonly database` in the status bar and keeps the draft | unchanged (probed headless, not a test) |
| Malformed `golded.toml` | traceback (`TOMLDecodeError`), exit 1 | `Cannot read config …: Illegal character …`, exit 1 |
| Invalid `from_address` | traceback (`ValueError`), exit 1 | `Cannot read config …: Invalid FTN address [nonsense].`, exit 1 |
| `--config` names a directory | ignored, defaults used | unchanged |
| `threaded_list = "no"` | read with `bool()`, so any non-empty string meant `true` | `Cannot read config …: threaded_list must be true or false, not 'no'`, exit 1 |
| `theme = "neon"` | fell back to `dark` without a message | `Cannot read config …: theme must be one of dark, light, not 'neon'`, exit 1 |
| `splash_seconds = -1` (option added 2026-11-15) | did not exist; countdown fixed at 10 | `Cannot read config …: splash_seconds must be a whole number of 0 or more, not -1`, exit 1 |

The last two were accepted silently before; Odinn decided on 2026-11-14 that they
are errors. Covered by `tests/test_user_config.py`.

## Pagebar and mouse wheel (2026-11-14)

The list screens updated the pagebar only when the cursor moved; the old
`on_scroll` handler never ran. Probe: 45 messages in a 15-row terminal, 15
`MouseScrollDown` events on the table moved `scroll_y` from 0 to 30 with the
cursor on row 0 and produced 0 pagebar updates. The list screens now watch the
table's `scroll_y`, as the message view already did for its body; the same probe
gives 15 updates and a pagebar equal to a fresh repaint.
`test_pagebar_follows_list_scroll` fails without the fix and passes with it.

## Manual terminal checks

Odinn tested iTerm2, macOS Terminal and Ubuntu 24.04 in Multipass on
2026-11-21 with synthetic databases.
He reported that the guided checks worked in all three terminals.

| Check | macOS Terminal | iTerm2 | Linux terminal |
| --- | --- | --- | --- |
| `F2` saves | Pass (reported) | Pass (reported) | Pass (reported) |
| `Ctrl+S` saves | Pass (reported) | Pass (reported) | Pass (reported) |
| `Cmd+S` saves (may not reach the app) | Pass (reported) | Pass (reported) | Not part of the Linux test |
| `F9` toggles theme; both themes readable | Pass (reported) | Pass (reported) | Pass (reported) |
| `Shift+→` / `Shift+←` in the message view | Pass (reported) | Pass (reported) | Pass (reported) |
| `Shift+Space` pages up | Pass (reported) | Pass (reported) | Pass (reported) |
| Mouse wheel moves the pagebar in the lists and the message view | Pass (reported) | Pass (reported) | Pass (reported) |
| Resize while in each screen | Pass (reported) | Pass (reported) | Pass (reported) |
| 80×25 shows every screen without clipping | Pass (reported) | Pass (reported) | Pass (reported) |
