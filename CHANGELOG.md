# Changelog

## 1.1.0 — 2026-11-23

- Browse and write new messages and replies in JAM, Squish, FTSC MSG, Opus
  and Hudson areas alongside SQLite.
- Define mixed-format areas in `golded.toml` or open a classic `AREADEF`
  configuration with `--area-config`. Hudson areas select an individual
  board in a shared base.
- Browse with `--readonly` to disable writes. A read-only Hudson session
  loads each shared base once at startup.
- Configure strict or lenient JAM reads and strict, archive or lenient
  Squish reads. Squish archive mode automatically protects the area against
  writes. Squish also supports an explicit `allow_unlinked_append` write
  mode and startup diagnostics via `--debug`.
- Require golded-ftn 1.5.2 or later so Windows releases writer lock handles
  after use.
- The manual documents each format and the supported configuration syntax.

## 1.0.0 — 2026-11-21

First public release, from the GoldED.py terminal reader.

- Read echomail and netmail areas from one golded-ftn-sqlite base; write new
  messages and replies with GoldED-style quoting, tearline and Origin.
- Flat or threaded message list, subject-thread stepping and display-only mojibake
  repair.
- Dark and light themes.
- Linux, macOS and Windows; Windows is tested headless in CI.
- `golded.toml` for name, FTN address, base, Origin, theme, threaded list and the
  splash countdown (`splash_seconds`, new in this release); `--config`,
  `--database` and `--theme` options.
- A missing or unsupported base, or a config golded cannot use, stops at startup
  with one line and exit status 1.
- The list pagebar follows mouse-wheel scrolling.
- Brackets in area names show as text instead of being read as markup.
- HTML manual in `site/`.
