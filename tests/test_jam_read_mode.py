from pathlib import Path
from struct import pack, pack_into

import pytest
from golded_ftn import OutgoingMessage
from golded_ftn_jam import JamWriter

from golded.data.store import open_configured_store
from golded.logic.session import Session


def legacy_jam(base: Path) -> Path:
    writer = JamWriter()
    writer.create(base)
    with writer.open(base) as jam:
        jam.append(
            OutgoingMessage(
                from_name="Alice",
                to_name="All",
                subject="Legacy",
                body_text="Original message",
            )
        )
    header = base.with_suffix(".JHR")
    raw = bytearray(header.read_bytes())
    offset = int.from_bytes(base.with_suffix(".JDX").read_bytes()[4:8], "little")
    subfields = int.from_bytes(raw[offset + 8 : offset + 12], "little")
    payload = b"NOTE: " + b"x" * 256
    raw.extend(pack("<HHI", 2000, 0, len(payload)) + payload)
    pack_into("<I", raw, offset + 8, subfields + 8 + len(payload))
    header.write_bytes(raw)
    return header


def test_jam_global_mode_area_override_and_strict_writer(tmp_path: Path) -> None:
    header = legacy_jam(tmp_path / "archive")
    JamWriter().create(tmp_path / "empty")
    definition = 'AREADEF ARCHIVE "Archive" 0 Echo JAM archive . ()\n'
    config = tmp_path / "golded.cfg"
    config.write_text(definition)
    with pytest.raises(ValueError, match="Subfield 2000 exceeds"):
        open_configured_store(config)

    config.write_text("JAMREAD lenient\nJAMREAD ARCHIVE strict\n" + definition)
    with pytest.raises(ValueError, match="Subfield 2000 exceeds"):
        open_configured_store(config)

    config.write_text(
        definition + 'AREADEF EMPTY "Empty" 0 Echo JAM empty . ()\n'
        "JAMREAD lenient\nJAMREAD EMPTY strict ; override\n"
    )
    session = Session(open_configured_store(config))
    assert session.area_read_status("EMPTY") == ""
    session.select_area("ARCHIVE")
    assert [item.subject for item in session.messages()] == ["Legacy"]
    assert (
        session.area_read_status("ARCHIVE")
        == "JAM lenient: 1 recovered, 0 skipped, 0 stopped"
    )
    session.start_draft_message()
    session.set_draft_message(
        OutgoingMessage(
            from_name="Tester", to_name="All", subject="New", body_text="New"
        )
    )
    original = {p: p.read_bytes() for p in tmp_path.glob("archive.J*")}
    assert header in original
    with pytest.raises(RuntimeError, match="Subfield 2000 exceeds"):
        session.save_draft_message()
    assert session.draft_message() is not None
    assert {p: p.read_bytes() for p in original} == original

    config.write_text("JAMREAD ARCHIVE lenient\nJAMREAD strict\n" + definition)
    assert open_configured_store(config).message("ARCHIVE", 1).subject == "Legacy"


def test_lenient_partial_coverage_is_visible_in_area_list(tmp_path: Path) -> None:
    from asyncio import run

    from textual.widgets import Static

    from golded.logic.user_config import UserConfig
    from golded.ui.app import GoldED

    base = tmp_path / "archive"
    legacy_jam(base)
    index = base.with_suffix(".JDX")
    original_record = index.read_bytes()
    # A header offset into the area header is unparseable, and a reused
    # offset stops traversal rather than risking duplicate messages.
    index.write_bytes(original_record + pack("<II", 0, 4) + original_record)
    config = tmp_path / "golded.cfg"
    config.write_text(
        'JAMREAD lenient\nAREADEF ARCHIVE "Archive" 0 Echo JAM archive . ()\n'
    )
    session = Session(open_configured_store(config), UserConfig(splash_seconds=0))
    app = GoldED(session, "dark")

    async def check_status() -> None:
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            status = str(app.screen.query_one("#status-middle", Static).render())
            assert "JAM lenient: 1 recovered, 1 skipped, 1 stopped" in status

    run(check_status())


@pytest.mark.parametrize(
    ("global_mode", "area_mode", "recovers"),
    [
        (None, None, False),
        ("lenient", None, True),
        ("lenient", "strict", False),
        ("strict", "lenient", True),
    ],
)
def test_toml_jam_read_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    global_mode: str | None,
    area_mode: str | None,
    recovers: bool,
) -> None:
    from unittest.mock import Mock

    from golded import cli

    legacy_jam(tmp_path / "archive")
    config = tmp_path / "golded.toml"
    jam = f'[jam]\nread_mode = "{global_mode}"\n' if global_mode else ""
    override = f', read_mode = "{area_mode}"' if area_mode else ""
    config.write_text(
        jam + '[areas]\nARCHIVE = { description = "Archive", group = "0", '
        f'type = "echo", format = "jam", path = "archive"{override} }}\n'
    )
    monkeypatch.setattr("sys.argv", ["golded", "--config", str(config)])
    run = Mock()
    monkeypatch.setattr(cli, "run", run)
    if recovers:
        cli.main()
        store, _, _ = run.call_args.args
        assert store.message("ARCHIVE", 1).subject == "Legacy"
        assert (
            store.read_status("ARCHIVE")
            == "JAM lenient: 1 recovered, 0 skipped, 0 stopped"
        )
    else:
        with pytest.raises(SystemExit) as error:
            cli.main()
        assert error.value.code == 1
        assert "Subfield 2000 exceeds" in capsys.readouterr().err
        run.assert_not_called()
