# Changelog

## 1.0.0 — unreleased

First public release, from the GoldED.py terminal reader.

- Read echomail and netmail areas from one golded-ftn-sqlite base; write new
  messages and replies with GoldED-style quoting, tearline and Origin.
- Flat or threaded message list, subject-thread stepping and display-only mojibake
  repair.
- Dark and light themes.
- `golded.toml` for name, FTN address, base, Origin, theme, threaded list and the
  splash countdown (`splash_seconds`, new in this release); `--config`,
  `--database` and `--theme` options.
- A missing or unsupported base, or a config golded cannot use, stops at startup
  with one line and exit status 1.
- The list pagebar follows mouse-wheel scrolling.
- Brackets in area names show as text instead of being read as markup.
- HTML manual in `site/`.
