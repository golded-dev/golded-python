from pathlib import Path

import pytest
from golded_ftn import OutgoingMessage

from golded.data.area import Area
from golded.data.store import create_message_store, open_configured_store
from golded.logic.session import Session
from golded.logic.user_config import UserConfig


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
            'AREADEF ONE "Classic" A Echo Hudson 21 . ()',
            "unsupported message-base format Hudson",
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
