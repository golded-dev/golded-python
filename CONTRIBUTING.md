# Contributing

Use Python 3.12+ and uv. The UI works through `logic.Session`; the FTN packages are
reached only through `golded.data`. Add a test before changing quoting, threading,
navigation or what gets saved; drive screens headless with Textual's `run_test`.

Run:

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python scripts/check_pages.py
uv build --no-sources
uv run twine check dist/*
uv run python scripts/verify_distribution.py
```

A change to a key binding, a config field or a screen also changes the manual:
edit `scripts/build_pages.py`, run `scripts/build_screenshots.py` when a screen
changed, then `scripts/build_pages.py`, and commit `site/` and `docs/screens/`.
`check_pages.py` fails when the pages are stale or the keys page and the bindings
disagree.

Use synthetic messages, such as the demo seeder's. Keep private message bases,
operator configuration, credentials and access material out of tests and
distributions. See [release preparation](docs/release.md).
