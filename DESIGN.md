# golded manual design

Read this file before editing the manual in `site/`. The design follows
[GoldED for Python DESIGN.md](https://github.com/golded-dev/golded-ftn-python-docs/blob/main/DESIGN.md)
and the `golded-ftn-tools` manual: same shell, palette, fonts, navigation,
copy buttons and print rules. This file records only what differs.

## Build

`scripts/build_pages.py` writes all five pages. Do not edit `site/*.html` by
hand. `scripts/check_pages.py` fails when a page is stale, and it checks IDs,
links, local assets, remote resources and the key list.

| Page | Content |
| --- | --- |
| `index.html` | What it is, install, first run |
| `database.html` | The SQLite base, `ftnt` 1.2.0 to create one, the demo seeder, open errors |
| `config.html` | `golded.toml` (embedded from `golded.toml.example`), CLI options, invalid values |
| `keys.html` | Every key per screen |
| `screens.html` | Each screen in both themes |

`RELEASED` in `build_pages.py` switches the bar, footer and install section
from "not released" (install from a checkout) to the PyPI install. Flip it
only after `golded` is installable from PyPI.

## Assets

`site/assets/manual.css`, `golded-logo.png` and `OFL.txt` are copied
unchanged from `golded-ftn-tools`; `manual.css` embeds IBM Plex Sans and Mono.
Keep them identical to the sibling. `golded.css` holds this manual's additions:
`kbd` and the screenshot grid.

## Keys

Each row in `KEYS` names the code bindings it documents (`Class:key`). The
check compares them with the `BINDINGS` of the app and screens, both ways.
Keys handled in `on_key` or by `DataTable` (arrows and Enter in lists, filter
letters, the splash's any key) have no binding and are listed without one.

## Screenshots

`scripts/build_screenshots.py` renders `docs/screens/*.svg` at 80×25 from the
demo base, with the clock frozen at 09:41, so a rerun gives the same bytes
unless the UI changed. Textual's export loads Fira Code from a CDN; the script
removes those font rules and the SVG text uses IBM Plex Mono. The pages inline
the SVGs (an SVG in `<img>` cannot use the page's fonts) and add `role="img"`
with a label. Rebuild the screenshots, then the pages, after a UI change.

## Verification

Report only what was checked. Checked 2026-11-14 in Chrome: desktop at 1360 px,
and all five pages at 390 px mobile with no horizontal page scroll; fonts load
from `manual.css` and the screenshot text renders in IBM Plex Mono. Not checked:
Safari, print, keyboard-only navigation.
