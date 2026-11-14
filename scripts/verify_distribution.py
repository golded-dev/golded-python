"""Inspect and rebuild the distribution, then test the wheel outside the checkout.

Run after `uv build --no-sources`. Set GOLDED_WHEELHOUSE to install golded's
dependencies from a reviewed wheelhouse; otherwise they come from the public index.
Linux and macOS only.
"""

from __future__ import annotations

import email
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_REQUIREMENTS = ["Faker>=40.43.0", "pytest>=8"]


def run(args: list[str], cwd: Path) -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def check_wheel(wheel: Path, project: dict[str, str]) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = email.message_from_bytes(
            archive.read(next(n for n in names if n.endswith("/METADATA")))
        )
        entry_points = archive.read(
            next(n for n in names if n.endswith("/entry_points.txt"))
        ).decode()
    assert metadata["Name"] == project["name"]
    assert metadata["Version"] == project["version"]
    assert metadata["License-Expression"] == "MIT"
    assert "golded = golded.cli:main" in entry_points
    assert "golded/py.typed" in names
    assert any(n.endswith("/licenses/LICENSE") for n in names)
    assert not any("file:" in d for d in metadata.get_all("Requires-Dist", []))
    assert not any(n.startswith(("tests/", "scripts/")) for n in names)


def extract_sdist(sdist: Path, work: Path) -> Path:
    with tarfile.open(sdist) as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            assert not Path(member.name).is_absolute() and ".." not in parts
            assert not {".env", ".git", ".venv", "__pycache__"}.intersection(parts)
            assert not member.name.endswith((".sqlite3", "golded.toml"))
        archive.extractall(work, filter="data")
    (source,) = work.iterdir()
    return source


def check_consumer(candidate: Path, source: Path, env: Path, work: Path) -> None:
    run(["uv", "venv", "--python", sys.executable, str(env)], work)
    python = str(env / "bin/python")
    install = ["uv", "pip", "install", "--python", python, "--no-cache", "--reinstall"]
    if os.environ.get("GOLDED_WHEELHOUSE"):
        install += ["--find-links", os.environ["GOLDED_WHEELHOUSE"]]
    run(install + [str(candidate)], work)
    run(["uv", "pip", "check", "--python", python], work)
    run(
        [
            python,
            "-I",
            "-c",
            "import golded; assert 'site-packages' in golded.__file__",
        ],
        work,
    )
    run([str(env / "bin/golded"), "--help"], work)

    # Run the sdist's tests, headless app tests included, against the installed
    # wheel. Without src/ on disk, every golded import must come from site-packages.
    tests = work / f"{env.name}-tests"
    shutil.copytree(source, tests, ignore=shutil.ignore_patterns("src", "dist"))
    run(["uv", "pip", "install", "--python", python, *TEST_REQUIREMENTS], work)
    run([python, "-m", "pytest", "-q", "-p", "no:cacheprovider"], tests)


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    (wheel,) = (ROOT / "dist").glob("*.whl")
    (sdist,) = (ROOT / "dist").glob("*.tar.gz")
    check_wheel(wheel, project)

    with tempfile.TemporaryDirectory(prefix="golded-distribution-") as temporary:
        work = Path(temporary)
        source = extract_sdist(sdist, work)
        config = tomllib.loads((source / "pyproject.toml").read_text())
        assert "sources" not in config.get("tool", {}).get("uv", {})

        run(["uv", "build", "--no-sources", "--wheel"], source)
        (rebuilt,) = (source / "dist").glob("*.whl")
        with zipfile.ZipFile(wheel) as first, zipfile.ZipFile(rebuilt) as second:
            assert set(first.namelist()) == set(second.namelist())
            assert all(first.read(n) == second.read(n) for n in first.namelist())

        for index, candidate in enumerate([wheel, rebuilt]):
            check_consumer(candidate, source, work / f"consumer-{index}", work)

    print(
        "Metadata, contents, sdist rebuild, two clean installs and the test suite "
        "against each installed wheel passed."
    )


if __name__ == "__main__":
    main()
