"""Check the manual in site/: structure, links, freshness and key bindings.

No browser is involved; layout, fonts and print need a look in one.
"""

from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from textual.binding import Binding

import build_pages
from golded.ui.app import GoldED
from golded.ui.area_list import AreaListScreen
from golded.ui.message_list import MessageListScreen
from golded.ui.message_view import MessageViewScreen
from golded.ui.write_message import DiscardDialog, WriteMessageScreen

SITE = build_pages.SITE
BOUND = (
    GoldED,
    AreaListScreen,
    MessageListScreen,
    MessageViewScreen,
    WriteMessageScreen,
    DiscardDialog,
)


class Page(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.resources: list[str] = []
        self.copies: list[str] = []
        self.bindings: list[str] = []
        self.current = 0
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if identity := attributes.get("id"):
            assert identity not in self.ids, f"duplicate ID: {identity}"
            self.ids.add(identity)
        if link := attributes.get("href"):
            (self.links if tag == "a" else self.resources).append(link)
        if source := attributes.get("src"):
            self.resources.append(source)
        if target := attributes.get("data-copy"):
            self.copies.append(target)
        if bindings := attributes.get("data-bindings"):
            self.bindings.extend(bindings.split())
        if attributes.get("aria-current") == "page":
            self.current += 1


def code_bindings() -> set[str]:
    found = set()
    for owner in BOUND:
        for binding in owner.BINDINGS:
            keys = binding.key if isinstance(binding, Binding) else binding[0]
            for key in keys.split(","):
                found.add(f"{owner.__name__}:{key.strip()}")
    return found


def main() -> None:
    expected = {
        "index.html": build_pages.index_page(),
        "database.html": build_pages.database_page(),
        "config.html": build_pages.config_page(),
        "keys.html": build_pages.keys_page(),
        "screens.html": build_pages.screens_page(),
    }
    on_disk = {path.name for path in SITE.glob("*.html")}
    assert on_disk == set(expected), f"pages on disk: {sorted(on_disk)}"

    pages = {}
    for name, text in expected.items():
        source = (SITE / name).read_text(encoding="utf-8")
        assert source == text, f"{name} is stale; run scripts/build_pages.py"
        pages[name] = Page(source)

    for name, page in pages.items():
        assert page.current == 1, name
        assert all(copy in page.ids for copy in page.copies), name
        for resource in page.resources:
            target = urlsplit(resource)
            assert not (target.scheme or target.netloc), (name, resource)
            assert (SITE / unquote(target.path)).is_file(), (name, resource)
        for link in page.links:
            target = urlsplit(link)
            if target.scheme or target.netloc:
                continue
            path = unquote(target.path) or name
            assert (SITE / path).is_file(), (name, link)
            if target.fragment:
                assert unquote(target.fragment) in pages[path].ids, (name, link)
        text = (SITE / name).read_text(encoding="utf-8").lower()
        for banned in ("plan.md", "verification.md", "cdnjs", "fonts.googleapis"):
            assert banned not in text, (name, banned)

    documented = pages["keys.html"].bindings
    assert len(documented) == len(set(documented)), "a binding is listed twice"
    missing = code_bindings() - set(documented)
    extra = set(documented) - code_bindings()
    assert not missing, f"bindings in the code but not in keys.html: {sorted(missing)}"
    assert not extra, f"bindings in keys.html but not in the code: {sorted(extra)}"

    print(
        f"{len(pages)} pages: current with their sources, unique IDs, one page "
        "marker each, copy targets, local links and assets, no remote resources."
    )
    print(
        f"keys.html lists the {len(documented)} key bindings declared in the code. "
        "No browser check was run."
    )


if __name__ == "__main__":
    main()
