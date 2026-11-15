# Release preparation

Version 1.0.0 targets Linux, macOS and Windows, Python 3.12–3.14. CI must pass on
all three. Windows is tested headless only; nobody has run it in a Windows
terminal, so say so if a Windows bug report comes in.

## Verification

1. On the release commit, run every check in [CONTRIBUTING.md](../CONTRIBUTING.md)
   with `uv sync --locked --no-sources` on Python 3.12 and 3.14. CI runs the same
   checks on Linux, macOS and Windows with 3.12, 3.13 and 3.14.
2. Build wheel and sdist with `uv build --no-sources`. Rebuild the wheel from the
   sdist; `scripts/verify_distribution.py` does this and checks metadata, LICENSE,
   `py.typed`, the contents and two clean installs outside the checkout. Do not
   use editable installs or local source overrides.
3. Install the wheel in a clean venv outside the checkout and run `golded --help`
   and `golded --database DEMO` against a base from `scripts/seed_demo.py`.
4. Run the manual terminal checks in `docs/VERIFICATION.md` and fill in the table.
5. Recheck that the version is free at `https://pypi.org/pypi/golded/json`
   immediately before release. A released version must never be overwritten.
6. Set the date in `CHANGELOG.md`, then write `RELEASE-SHA256.txt` for the wheel and
   sdist. Changes after verification require rebuilding and checking the changed
   artifact.

## CI and Trusted Publishing

CI resolves public dependencies with `uv sync --locked --no-sources`. Do not point
CI at a private workspace or an unpinned sibling branch.

A maintainer must create and protect the GitHub `pypi` environment with required
reviewers, register the exact repository owner/name, workflow `publish.yml` and
environment `pypi` as the PyPI Trusted Publisher, and enable the repository's
Actions workflows. The `pypi` environment exists, requires the maintainer's
review and allows deployments from `main` only. `publish.yml` runs by hand with a
release tag: it downloads the reviewed GitHub release assets, verifies
`RELEASE-SHA256.txt`, then requests an OIDC identity. No API token is required or
included. This document does not create that configuration or prove it exists.

## Manual

`pages.yml` checks `site/` on every push and deploys it to GitHub Pages only from
`main` when the repository variable `PUBLISH_PAGES` is `true`. After the PyPI
upload:

1. Enable GitHub Pages with GitHub Actions as the source and set `PUBLISH_PAGES`.
2. Set `RELEASED = True` in `scripts/build_pages.py`, run it and
   `scripts/check_pages.py`, and commit `site/`.
3. Check the public manual in a browser, and link it from the suite docs
   (`golded-ftn-python-docs`).

## Publication

Each step is separately authorized: push the repository, configure the `pypi`
environment and Trusted Publisher, tag `v1.0.0` and create the GitHub release with
wheel, sdist and `RELEASE-SHA256.txt`, run the publish workflow, publish the
manual. After upload, run `uvx golded --help` from the public index without a
wheelhouse. Local success does not prove public installation.
