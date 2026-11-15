# golded

golded is a Textual terminal message reader for FidoNet echomail and netmail in one
golded-ftn-sqlite base, modelled on GoldED. It reads, writes new messages and
replies; other formats, editing, deleting and search are out of scope for 1.x.

Keep the layers: `cli.py` opens the store, `ui/` talks only to `logic.Session`, and
the FTN packages are reached only through `golded.data`. The config fields, CLI
options and key bindings are the public surface since 1.0.0. Text from a message
base goes to the screen as `Text` or with markup off, never as Textual markup.

Use TDD at the session, config, quoting and threading seams, and drive screens
headless with `run_test`. Run pytest, Ruff lint/format, strict mypy,
`scripts/check_pages.py` and `scripts/verify_distribution.py`. A change to keys,
config or a screen also rebuilds the manual in `site/` (see CONTRIBUTING.md). Use
synthetic messages, such as `scripts/seed_demo.py`'s, and keep private message
bases and operator configuration out of tests.

Edit this fragment or agent-compose.toml, then preview, build and check. Commits,
remotes, tags and publication require an explicit request.
