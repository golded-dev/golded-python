from pathlib import Path

import pytest
from golded_ftn import OutgoingMessage

from golded.data.area import Area
from golded.data.store import MessageStore, create_message_store, open_configured_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig, load_user_config


def test_session_routes_configured_areas_to_separate_databases(tmp_path: Path) -> None:
    first = create_message_store(tmp_path / "first base.sqlite3", [Area("ONE", "One")])
    second = create_message_store(
        tmp_path / "second.sqlite3", [Area("TWO", "Two"), Area("HIDDEN", "Hidden")]
    )
    first.append(
        "ONE",
        OutgoingMessage(
            from_name="Alice", to_name="All", subject="One", body_text="Hello"
        ),
    )
    second.append(
        "TWO",
        OutgoingMessage(
            from_name="Bob", to_name="All", subject="Two", body_text="Hello"
        ),
    )
    config = tmp_path / "golded.cfg"
    config.write_text(
        "AREAFILE Fastecho areas.bbs\n"
        'areadef TWO "Second; configured" #117 Echo SQLite second.sqlite3 . () ; note\n'
        'AREADEF ONE "First configured" A Echo SQLite "first base.sqlite3"\n',
        encoding="utf-8",
    )

    store = open_configured_store(config)
    session = Session(store, UserConfig(from_name="Carol"))
    assert [(area.code, area.name) for area in session.areas()] == [
        ("TWO", "Second; configured"),
        ("ONE", "First configured"),
    ]
    assert store.message("ONE", 1).subject == "One"
    session.select_area("TWO")
    assert [message.subject for message in session.messages()] == ["Two"]
    session.start_draft_message()
    session.set_draft_message(
        OutgoingMessage(
            from_name="Carol", to_name="All", subject="New", body_text="Hello"
        )
    )
    assert session.save_draft_message() == 2

    session.select_area("ONE")
    session.select_message(1)
    session.start_reply_draft("Hello")
    assert session.save_draft_message() == 2

    assert [message.subject for message in second.messages("TWO")] == ["Two", "New"]
    reply = first.message("ONE", 2)
    assert reply.subject == "Re: One"
    assert reply.reply_to_msgno == 1


@pytest.mark.parametrize(
    ("definition", "reason"),
    [
        ('AREADEF ONE "Missing path" A Echo SQLite', "malformed AREADEF"),
        ('AREADEF ONE "Bad group" #1000 Echo SQLite base.db', "invalid group"),
        ('AREADEF ONE "Bad type" A Else SQLite base.db', "unsupported area type"),
        (
            'AREADEF ONE "Classic" A Echo Squish base . ()',
            "unsupported message-base format Squish",
        ),
    ],
)
def test_invalid_area_reports_config_line(
    tmp_path: Path, definition: str, reason: str
) -> None:
    config = tmp_path / "golded.cfg"
    config.write_text(f"; comment\n{definition}\n", encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        open_configured_store(config)
    assert f"{config}:2:" in str(raised.value)
    assert reason in str(raised.value)


@pytest.mark.parametrize("toml", [False, True])
def test_msg_session_reads_writes_and_replies(tmp_path: Path, toml: bool) -> None:
    from golded_ftn_msg import MsgReader, MsgWriter

    base = tmp_path / "msg-area"
    writer = MsgWriter()
    writer.create(base)
    with writer.open(base) as opened:
        parent = opened.append(
            OutgoingMessage(
                from_name="Alice", to_name="All", subject="Original", body_text="Body"
            )
        ).identity.msgno

    create_message_store(tmp_path / "local.db", [Area("LOCAL", "Local")])
    if toml:
        config = tmp_path / "golded.toml"
        config.write_text(
            "[areas]\n"
            'LOCAL = { description = "Local", group = "A", type = "echo", '
            'format = "sqlite", path = "local.db" }\n'
            'MESSAGES = { description = "Messages", group = "B", type = "echo", '
            'format = "msg", path = "msg-area" }\n'
        )
        store = open_configured_store(config, entries=load_user_config(config).areas)
    else:
        config = tmp_path / "golded.cfg"
        config.write_text(
            'AREADEF LOCAL "Local" A Echo SQLite local.db\n'
            'AREADEF MESSAGES "Messages" B Echo MSG msg-area\n'
        )
        store = open_configured_store(config)
    session = Session(store, UserConfig(from_name="Carol"))
    assert [area.code for area in session.areas()] == ["LOCAL", "MESSAGES"]
    session.select_area("MESSAGES")
    assert [item.subject for item in session.messages()] == ["Original"]
    session.start_draft_message()
    session.set_draft_message(
        OutgoingMessage(
            from_name="Carol", to_name="All", subject="New", body_text="Blåbær"
        )
    )
    new = session.save_draft_message()
    session.select_message(parent)
    session.start_reply_draft("Body")
    reply = session.save_draft_message()

    messages = {item.msgno: item for item in MsgReader().read(base)}
    assert new is not None and "Blåbær" in messages[new].body_text
    assert messages[new].posted_at is not None
    assert reply is not None and messages[reply].reply_to_msgno == parent
    assert messages[reply].subject == "Re: Original"
    session.select_area("LOCAL")
    assert session.messages() == ()


def test_opus_readonly_via_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime

    from golded_ftn_msg import MsgWriter

    from golded import cli

    base = tmp_path / "opus"
    writer = MsgWriter()
    writer.create(base, header_format="opus")
    outgoing = OutgoingMessage(
        from_name="Alice",
        to_name="All",
        subject="Original",
        body_text="Text",
        posted_at=datetime(1992, 1, 22, 22, 43, 12),
    )
    with writer.open(base, header_format="opus") as opened:
        uid = opened.append(outgoing).identity.msgno
    config = tmp_path / "golded.toml"
    config.write_text(
        '[areas]\nTEST = { description = "Test", group = "A", type = "echo", '
        'format = "opus", path = "opus" }\n'
    )
    original = (base / "1.MSG").read_bytes()

    def verify(store: MessageStore, theme: str, config: UserConfig) -> None:
        session = Session(store, config)
        session.select_area("TEST")
        session.select_message(uid)
        assert session.readonly()
        message = session.current_message()
        assert message is not None and message.posted_at == outgoing.posted_at
        session.start_draft_message()
        session.start_reply_draft("Text")
        assert session.draft_message() is None
        with pytest.raises(PermissionError):
            store.append("TEST", outgoing)
        with pytest.raises(PermissionError):
            store.delete("TEST", uid)

    monkeypatch.setattr("sys.argv", ["golded", "--config", str(config), "--readonly"])
    monkeypatch.setattr(cli, "run", verify)
    cli.main()
    assert (base / "1.MSG").read_bytes() == original


@pytest.mark.parametrize("toml", [False, True])
def test_hudson_routes_distinct_boards(tmp_path: Path, toml: bool) -> None:
    from golded_ftn_hudson import HudsonReader, HudsonWriter

    base = tmp_path / "hudson"
    base.mkdir()
    writer = HudsonWriter()
    writer.create(base)
    for board in (7, 8):
        with writer.open(base, board=board) as opened:
            opened.append(
                OutgoingMessage(
                    from_name="Alice",
                    to_name="All",
                    subject=f"Board {board}",
                    body_text="Original",
                )
            )

    if toml:
        config = tmp_path / "golded.toml"
        config.write_text(
            "[areas]\n"
            'SEVEN = { description = "Seven", group = "A", type = "echo", '
            'format = "hudson", path = "hudson", board = 7 }\n'
            'EIGHT = { description = "Eight", group = "A", type = "echo", '
            'format = "hudson", path = "hudson", board = 8 }\n'
        )
        entries = load_user_config(config).areas
    else:
        config = tmp_path / "golded.cfg"
        config.write_text(
            'AREADEF SEVEN "Seven" A Echo Hudson 7\n'
            'AREADEF EIGHT "Eight" A Echo Hudson 8\n'
            'HUDSONPATH "hudson"\n'
        )
        entries = None
    store = open_configured_store(config, entries=entries)
    assert [area.code for area in store.areas()] == ["SEVEN", "EIGHT"]
    assert [message.subject for message in store.messages("SEVEN")] == ["Board 7"]
    assert [message.subject for message in store.messages("EIGHT")] == ["Board 8"]

    session = Session(store, UserConfig(from_name="Carol"))
    session.select_area("EIGHT")
    session.select_message(2)
    session.start_reply_draft("Original")
    reply = session.save_draft_message()
    session.start_draft_message()
    session.set_draft_message(
        OutgoingMessage(
            from_name="Carol", to_name="All", subject="New", body_text="Blåbær"
        )
    )
    new = session.save_draft_message()
    assert reply is not None and new is not None
    stored = {message.msgno: message for message in HudsonReader().read(base)}
    assert stored[reply].area == stored[new].area == "BOARD8"
    assert stored[reply].reply_to_msgno == 2
    assert "Blåbær" in stored[new].body_text
    assert [message.subject for message in store.messages("SEVEN")] == ["Board 7"]

    readonly = open_configured_store(config, entries=entries, readonly=True)
    assert readonly.area_readonly("EIGHT")
    assert readonly.message("EIGHT", reply).subject == "Re: Board 8"
    with pytest.raises(PermissionError):
        readonly.delete("EIGHT", reply)
