"""Build a fresh test database (deletes the target file and SQLite sidecars first)."""

from datetime import UTC, datetime
from pathlib import Path

from faker import Faker
from faker.providers import BaseProvider
from golded_ftn import FtnAddress, OutgoingMessage

from golded.data.area import Area
from golded.data.store import create_message_store


class FtnProvider(BaseProvider):
    def ftn_address(self) -> FtnAddress:
        point = None
        if self.generator.boolean(chance_of_getting_true=40):
            point = self.random_int(1, 99)

        return FtnAddress(
            zone=self.random_int(1, 6),
            net=self.random_int(1, 9999),
            node=self.random_int(1, 9999),
            point=point,
        )


def seed_database(path: str | Path) -> Path:
    path = Path(path)

    for candidate in (
        path,
        path.with_name(path.name + "-wal"),
        path.with_name(path.name + "-shm"),
    ):
        if candidate.exists():
            candidate.unlink()

    fake = Faker()
    fake.seed_instance(42)
    fake.add_provider(FtnProvider)

    store = create_message_store(
        path,
        areas=(
            Area("EMPTY", "Empty area"),
            Area("ONE", "Area with one message"),
            Area("HOLE", "Area with a hole"),
            Area("LONG", "Area with a very long message"),
            Area("THREADED", "Area with threaded messages"),
            Area("NETMAIL", "Area with netmail messages", kind="netmail"),
        ),
    )

    store.append("ONE", create_message(fake, to_name="All"))

    msgnos = []
    msgnos.append(store.append("HOLE", create_message(fake)))
    msgnos.append(store.append("HOLE", create_message(fake)))
    msgnos.append(store.append("HOLE", create_message(fake)))
    msgnos.append(store.append("HOLE", create_message(fake)))
    store.delete("HOLE", msgnos[2])

    long_body = "\n\n".join(fake.paragraphs(nb=60))
    store.append(
        "LONG",
        create_message(
            fake,
            to_name="All",
            subject="A very long message (scroll test)",
            body_text=long_body,
        ),
    )

    # Alice
    # ├─ Bob
    # │  └─ Diana
    # └─ Clara
    alice = store.append(
        "THREADED",
        create_message(
            fake,
            from_name="Alice",
            to_name="All",
            subject="First message",
        ),
    )
    store.append(
        "THREADED",
        create_message(
            fake,
            from_name="Mark Marksen",
            to_name="All",
            subject="Totally unrelated",
        ),
    )
    bob = store.append(
        "THREADED",
        create_message(
            fake,
            from_name="Bob",
            to_name="Alice",
            subject="Re: First message",
            reply_to_msgno=alice,
        ),
    )
    store.append(
        "THREADED",
        create_message(
            fake,
            from_name="Clara",
            to_name="Alice",
            subject="Re: First message",
            reply_to_msgno=alice,
        ),
    )
    store.append(
        "THREADED",
        create_message(
            fake,
            from_name="Diana",
            to_name="Bob",
            subject="Re: First message",
            reply_to_msgno=bob,
        ),
    )

    store.append(
        "NETMAIL",
        create_message(
            fake,
            from_address=fake.ftn_address(),
            to_address=fake.ftn_address(),
        ),
    )

    return path


def create_message(
    fake: Faker,
    from_name: str | None = None,
    to_name: str | None = None,
    subject: str | None = None,
    body_text: str | None = None,
    reply_to_msgno: int | None = None,
    from_address: FtnAddress | None = None,
    to_address: FtnAddress | None = None,
) -> OutgoingMessage:
    if from_name is None:
        from_name = fake.name()

    if to_name is None:
        to_name = fake.name()

    if subject is None:
        subject = fake.sentence(nb_words=4)

    if body_text is None:
        body_text = fake.paragraph(nb_sentences=3)

    if from_address is None:
        from_address = fake.ftn_address()

    return OutgoingMessage(
        posted_at=datetime(2026, 10, 28, 7, 9, 13, tzinfo=UTC),
        from_name=from_name,
        to_name=to_name,
        subject=subject,
        body_text=body_text,
        reply_to_msgno=reply_to_msgno,
        from_address=from_address,
        to_address=to_address,
    )


if __name__ == "__main__":
    from golded.cli import DEFAULT_DATABASE

    target = Path(DEFAULT_DATABASE)
    seed_database(target)
    print(f"Seeded {target}")
