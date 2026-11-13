# Release plan: golded 1.0.0 (repo golded-python)

Status: draft 2026-11-13. Nothing is committed or published yet.

Goal: turn the imported exam project into a release-ready open source package in
the golded-dev suite. No new features. "Release-ready" means the same bar as the
`golded-ftn-*-python` packages and `golded-ftn-tools`: installable wheel and sdist,
CI on Linux/macOS with Python 3.12–3.14, strict checks, a reviewed release
checklist, and a static HTML manual in the shared GoldED design.

Template repos: `golded-ftn-tools` (application with an HTML manual, entry point,
release checklist) and `golded-ftn-sqlite-python` (pyproject, CI, verify script).

## Starting point

- 41 files from the exam submission, flat layout: `app.py`, `ui/`, `logic/`,
  `data/`, `seed.py`, `tests/` (unittest, 63 tests passing on Python 3.14).
- Runtime: Textual 8.2.8, golded-ftn 1.5.1, golded-ftn-sqlite 1.1.0. Faker only in
  `seed.py`. All pinned with `==` in `requirements.txt`.
- Course-only seed content and personal names are already removed.
- README was the Danish course version; rewritten in English and its conda instructions
  were replaced with uv on 2026-11-13; see "Anaconda" below.
- Code style is the course idiom: `keyword = value` spacing, no Ruff, no mypy.

## Anaconda

The course required Anaconda; this project does not. The code never depended on
it: on 2026-11-13 the 63 tests passed on uv-managed CPython 3.14.10
(`--python-preference only-managed`, `/opt/anaconda3` off `PATH`) with only
`requirements.txt` installed. The README's conda instructions are replaced with uv.
Rules that keep it out:

- uv is the only documented toolchain (README, manual, CONTRIBUTING, AGENTS.md).
- CI runs on stock GitHub runners with `astral-sh/setup-uv`; no conda action.
- Phase 7 adds `grep -riE "conda|anaconda"` over the release tree; the only allowed
  hits are this section and the CHANGELOG line noting the change.

## Decisions before work starts

| # | Decision | Recommendation |
| --- | --- | --- |
| D1 | Names: distribution, import package, command | **Decided 2026-11-13:** `golded` / `golded` / `golded`, following the suite rule: the repo carries the `-python` suffix, the distribution does not (`golded-ftn-sqlite-python` → `golded-ftn-sqlite`). No clash with the C++ build, whose binaries are `gedlnx`/`gedmac`. `golded` is free on PyPI (checked 2026-11-13: 404). |
| D2 | What happens to `seed.py` | Move to `scripts/seed_demo.py`; Faker becomes a dev dependency. The manual shows how to create a real base with `ftnt`. Making seeding a CLI subcommand would be a new feature. |
| D3 | Adopt Ruff format | Yes. It rewrites the `keyword = value` course style once; do it in its own commit so the diff is reviewable as "format only". |
| D4 | mypy strictness | `strict = true`, as in the siblings. Textual typing may need a few targeted ignores; each one gets a reason. |
| D5 | Python floor | 3.12, as in the siblings. CI proves it. |
| D6 | LICENSE copyright holder | `GoldED.dev contributors`, as in the siblings. Odinn's call as the sole author. |
| D7 | Splash identity: `RELEASE_NAME` "Stille og roligt™ edition", `COPYRIGHT_YEARS` "1990 - 2026", `AUTHOR`, countdown 10 s | Keep as product identity; set the countdown deliberately (10 in the submission, 60 in the uncommitted course checkout). |
| D8 | Version | 1.0.0. The config format, CLI options and key bindings become the public surface. |
| D9 | Manual hosting | `site/` in this repo, published to GitHub Pages by a pinned workflow; linked from the suite docs (`golded-ftn-python-docs`). |

## Phase 1 — Baseline commit

1. Commit the imported tree unchanged apart from the course cleanup already done,
   with a message stating its origin (exam project, Itucation, 30 October 2026).
2. Add `docs/PLAN.md` (this file) in the same or the next commit.

Done when: `git log` shows one baseline commit and tests still pass.

## Phase 2 — Packaging

1. Move code to `src/golded/` with subpackages `ui`, `logic`, `data`.
   Imports become absolute package imports (`from golded.logic.session import …`).
2. `app.py` becomes `golded/cli.py` with `main()`; add `__main__.py` so
   `python -m golded` works. Entry point `golded = "golded.cli:main"`.
3. `pyproject.toml` modelled on `golded-ftn-tools`: hatchling, `requires-python >=3.12`,
   MIT, classifiers, project URLs, `py.typed`, sdist include list.
   Dependencies as ranges: `textual>=8.2.8,<9`, `golded-ftn>=1.5.1,<2`,
   `golded-ftn-sqlite>=1.1.0,<2`. Dev group: pytest, ruff, mypy, build, twine,
   hatchling, Faker.
4. Single version source: keep `logic/version.py` and add a test that it equals
   the installed distribution version (no behaviour change).
5. Delete `requirements.txt`; add `uv.lock`.
6. Behaviour stays as it is: `golded.toml` and `messages.sqlite3` are still
   resolved relative to the working directory. Only the error hint changes from
   "python seed.py" to a pointer to the manual.

Done when: `uv sync`, `uv run golded --help` and `uv run pytest` work from a clean clone.

## Phase 3 — Quality gates

1. pytest runs the existing unittest suite unchanged (no rewrite to pytest style).
2. Ruff lint (`E, F, I, UP, B`) and Ruff format; fix lint findings without
   changing behaviour.
3. mypy strict over `src`, `tests`, `scripts`.
4. Headless smoke tests with Textual's `App.run_test()` against a temporary
   seeded base: splash dismiss, open area, open message, next/previous,
   theme toggle, write and save a message, discard confirm. These test existing
   behaviour; they are the only way CI sees the UI at all.
5. `scripts/verify_distribution.py` adapted from `golded-ftn-tools`: build, rebuild
   wheel from sdist, inspect metadata and contents, install outside the checkout,
   run `golded --help` and the headless smoke against the installed wheel.
6. `.github/workflows/ci.yml`: Ubuntu + macOS × 3.12/3.13/3.14, `uv sync --no-sources`,
   ruff, mypy, pytest, build, `twine check`, verify script. Actions pinned to full SHAs.

Done when: all gates pass locally on 3.12 and 3.14.

## Phase 4 — Code review pass (no features)

1. Search for course leftovers: Danish strings in UI/comments/docstrings,
   "kursist", "Itucation", "eksamen", teacher or classmate names.
2. Review the error paths users will hit outside the course: missing database,
   non-SQLite file, read-only file, schema version mismatch from golded-ftn-sqlite,
   malformed `golded.toml`, invalid `from_address`. Each must give a one-line
   message and exit code 1, not a traceback. Bugs found here are fixed; missing
   features are listed under "Later".
3. Manual run in macOS Terminal, iTerm2 and one Linux terminal: key bindings
   (`Cmd+S` only reaches the app in some terminals; `F2`/`Ctrl+S` must always work),
   resize, both themes, 80×25 minimum.
4. Record results in `docs/VERIFICATION.md`.

## Phase 5 — HTML manual

Same construction as the `golded-ftn-tools` manual: plain HTML and CSS, little
JavaScript, readable without it, local assets only.

1. `DESIGN.md` pointing to the suite `DESIGN.md` in `golded-ftn-python-docs`;
   `site/assets/` with the GoldED logo, `manual.css`, IBM Plex fonts and `OFL.txt`.
2. Pages:
   - `index.html` — what it is, install (`uv tool install golded`,
     `pipx`), first run, link to the suite docs.
   - `database.html` — what a message base is here; creating one with `ftnt`
     (golded-ftn-sqlite format), the demo seeder for contributors.
   - `config.html` — `golded.toml` fields and the three CLI options.
   - `keys.html` — every key binding per screen.
   - `screens.html` — screenshots of each screen in both themes, generated as SVG
     by Textual from the deterministic demo base.
3. `scripts/build_pages.py` renders the pages from source text in `docs/manual/`;
   `scripts/check_pages.py` checks internal links, asset references, and that
   `keys.html` lists exactly the bindings declared in the code. That last check
   keeps the manual from drifting.
4. `.github/workflows/pages.yml` publishes `site/` only, on push to `main`.
5. Check a narrow mobile viewport, keyboard navigation and print view.
6. In `golded-ftn-python-docs`: link to the manual from the home page. Separate
   repo, separate commit.

## Phase 6 — Repository documents

- `README.md` in English: what, install, run, config summary, link to the manual.
  Short; the manual holds the details.
- `CHANGELOG.md` with `1.0.0 — <date>`.
- `CONTRIBUTING.md`, `SECURITY.md` following the siblings.
- `AGENTS.md` via `agent-compose` (`.agent-fragments/`, `agent-compose.toml`),
  replacing the course rule (kursist idiom) with suite rules: uv, pytest, Ruff,
  mypy, synthetic data only, no private archives in tests.
- `docs/release.md`: the release checklist below.
- `.gitignore` extended with `.venv/`, `dist/`, caches, `site/` build output
  only if generated pages are not committed (decide with D9; the siblings commit them).

## Phase 7 — Release verification

1. All Phase 3 gates on the release commit.
2. `uv build --no-sources`; rebuild wheel from sdist; `twine check`.
3. Install the wheel in a clean venv outside the checkout; run `golded --help`
   and the headless smoke.
4. Recheck that `golded` is still free on PyPI immediately before release.
5. Write `RELEASE-SHA256.txt` for wheel and sdist.

## Phase 8 — Publication (each step needs an explicit go)

1. Create `golded-dev/golded-python` on GitHub (public) and push `main`.
2. Create the protected `pypi` environment; register the PyPI Trusted Publisher
   (repo, `publish.yml`, environment `pypi`). Add `publish.yml` copied from
   `golded-ftn-tools` (downloads release assets, checks SHA-256, publishes via OIDC).
3. Tag `v1.0.0`, create the GitHub release with wheel, sdist and `RELEASE-SHA256.txt`.
4. Run the publish workflow.
5. Enable GitHub Pages; verify the public manual.
6. Verify from the public index: `uvx golded --help` without wheelhouse.
7. Link from the suite docs (Phase 5.6) once the manual is live.

## Out of scope (later)

Everything that changes what the program can do: other message-base formats
(JAM, Squish, MSG, Hudson), thread view stretch goals, editing/deleting
messages, search, user-level config locations (`~/.config`), packaging for
Homebrew, Windows support.
