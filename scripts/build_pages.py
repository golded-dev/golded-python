"""Build the public manual in site/: a front page and four topic pages.

The pages follow DESIGN.md. Screenshots come from docs/screens/, rendered by
scripts/build_screenshots.py, and are inlined so the SVG text can use the
manual's own fonts. Run scripts/check_pages.py afterwards.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from pathlib import Path

from golded.logic.user_config import DEFAULT_SPLASH_SECONDS
from golded.logic.version import VERSION

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SCREENS = ROOT / "docs" / "screens"
LIBRARY_DOCS = "https://golded-dev.github.io/golded-ftn-python-docs/"
FTNT_PYPI = "https://pypi.org/project/golded-ftn-tools/"

# Flip at release (Phase 8), after golded is installable from PyPI.
RELEASED = True
STATE = f"RELEASED {VERSION}" if RELEASED else f"{VERSION} · NOT RELEASED"

PAGES = (
    ("database", "Message bases"),
    ("config", "Configuration"),
    ("keys", "Keys"),
    ("screens", "Screens"),
)

# Copy buttons and section tracking, as in golded-ftn-tools.
SCRIPT = """
<script>
const contents=document.querySelector('.contents');
if(contents && window.matchMedia('(max-width:800px)').matches) contents.open=false;
for(const button of document.querySelectorAll('[data-copy]')){
  button.hidden=false;
  button.addEventListener('click', async () => {
    const node=document.getElementById(button.dataset.copy);
    const text=node.textContent;
    try {
      if(navigator.clipboard && window.isSecureContext){
        await navigator.clipboard.writeText(text);
      } else {
        const field=document.createElement('textarea');
        field.value=text;
        field.style.position='fixed';
        field.style.opacity='0';
        document.body.append(field);
        field.select();
        const ok=document.execCommand('copy');
        field.remove();
        button.focus();
        if(!ok) throw new Error('copy');
      }
      button.textContent='Copied';
    } catch {
      button.textContent='Select code';
      const range=document.createRange();
      range.selectNodeContents(node);
      const selection=window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    setTimeout(() => button.textContent='Copy code', 1800);
  });
}
const links=[...document.querySelectorAll('.nav a')];
const sections=[...document.querySelectorAll('main section')];
function markSection(id){
  for(const link of links){
    if(link.hash === '#' + id) link.setAttribute('aria-current','location');
    else link.removeAttribute('aria-current');
  }
}
function track(){
  if(!sections.length) return;
  let current=sections[0].id;
  for(const section of sections){
    if(section.getBoundingClientRect().top <= 120) current=section.id;
  }
  const page=document.scrollingElement;
  if(page.scrollHeight > page.clientHeight &&
     Math.ceil(page.scrollTop + page.clientHeight) >= page.scrollHeight - 2){
    current=sections[sections.length - 1].id;
  }
  markSection(current);
}
window.addEventListener('scroll', track, {passive:true});
window.addEventListener('resize', track);
window.addEventListener('hashchange', () => {
  const selected=links.find(link => link.hash === window.location.hash);
  if(selected) markSection(selected.hash.slice(1));
  else track();
});
track();
</script>
"""


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def code_pane(pane_id: str, label: str, text: str) -> str:
    return (
        f'<div class="code-pane" id="{esc(pane_id)}"><div class="code-head">'
        f"<span>{esc(label)}</span>"
        f'<button type="button" data-copy="{esc(pane_id)}-text" hidden>Copy code</button>'
        f'</div><pre><code id="{esc(pane_id)}-text">{esc(text)}</code></pre></div>'
    )


def table(head: tuple[str, ...], rows: Sequence[tuple[str, ...]]) -> str:
    """Cells are HTML; escape text before passing it in."""
    header = "".join(f"<th>{cell}</th>" for cell in head)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    return (
        f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def section(slug: str, number: str, title: str, body: str) -> str:
    return (
        f'<section class="guide-section" id="{esc(slug)}">'
        f'<div class="section-title"><span>{esc(number)}</span><h2>{esc(title)}</h2></div>'
        f"{body}</section>"
    )


Section = tuple[str, str, str, str]


def shell(
    filename: str,
    title: str,
    description: str,
    eyebrow: str,
    command: str,
    heading: str,
    lead: str,
    sections: list[Section],
) -> str:
    nav = ['<nav class="page-nav" aria-label="Manual">']
    home_current = ' aria-current="page"' if filename == "index.html" else ""
    nav.append(f'<a href="index.html"{home_current}>Home</a>')
    for name, label in PAGES:
        marker = ' aria-current="page"' if filename == f"{name}.html" else ""
        nav.append(f'<a href="{name}.html"{marker}>{esc(label)}</a>')
    nav.append("</nav>")
    contents = ['<details class="contents" open><summary>On this page</summary>']
    contents.append('<nav class="nav" aria-label="Sections">')
    for slug, number, heading_text, _body in sections:
        contents.append(
            f'<a href="#{esc(slug)}"><span class="num">{esc(number)}</span>'
            f"{esc(heading_text)}</a>"
        )
    contents.append("</nav></details>")
    main = [
        "<main>",
        f'<p class="eyebrow">{esc(eyebrow)}</p>',
        f'<p class="command">{esc(command)}</p>',
        f"<h1>{esc(heading)}</h1>",
        f'<p class="hero-lead">{lead}</p>',
    ]
    main.extend(section(*item) for item in sections)
    main.append("</main>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(description)}">
<title>{esc(title)}</title>
<link rel="stylesheet" href="assets/manual.css">
<link rel="stylesheet" href="assets/golded.css">
</head>
<body>
<a class="skip" href="#{esc(sections[0][0])}">Skip to content</a>
<div class="page">
<header class="masthead">
<a class="logo-mark" href="index.html" aria-label="golded home">
<img class="logo" src="assets/golded-logo.png" width="600" height="205" alt="GoldED">
<span class="logo-subtitle" aria-hidden="true">for the terminal</span>
</a>
<div><span>GoldED/Py</span><a href="{LIBRARY_DOCS}">Library docs ↗</a></div>
</header>
<div class="shell">
<div class="bar"><span>GOLDED / MESSAGE READER</span><span>{STATE} · PYTHON 3.12+</span></div>
<div class="layout">
<aside><div class="sidebar">
{"".join(nav)}
{"".join(contents)}
</div></aside>
{"".join(main)}
</div></div>
<footer><span>GoldED/Py / GoldED.dev</span><span>{STATE} · MIT LICENSE</span></footer>
</div>
{SCRIPT}
</body>
</html>
"""


def install_section() -> Section:
    if RELEASED:
        body = (
            "<p>Install from PyPI with Python 3.12 or newer, as a tool with its own "
            "environment:</p>"
            + code_pane("install-uv", "uv", "uv tool install golded\ngolded --help\n")
            + code_pane("install-pipx", "pipx", "pipx install golded\ngolded --help\n")
        )
    else:
        body = (
            "<p><strong>Not released yet.</strong> <code>golded</code> is not on "
            "PyPI. Until it is, install it from a checkout of the repository with "
            "Python 3.12 or newer:</p>"
            + code_pane(
                "install-checkout",
                "from a checkout",
                "uv tool install .\ngolded --help\n",
            )
        )
    body += (
        "<p>The command is <code>golded</code>; the package and import name are "
        "also <code>golded</code>. It runs on Linux, macOS and Windows; CI tests "
        "all three, and on Windows only headless.</p>"
    )
    return ("install", "00", "Install", body)


def index_page() -> str:
    pages = "".join(
        f'<li><a href="{name}.html">{esc(label)}</a> — {esc(blurb)}</li>'
        for (name, label), blurb in zip(
            PAGES,
            (
                "what golded opens, and how to make one",
                "golded.toml and the command-line options",
                "every key, screen by screen",
                "each screen in both themes",
            ),
            strict=True,
        )
    )
    sections = [
        install_section(),
        (
            "first-run",
            "01",
            "First run",
            "<p>By default, <code>golded</code> looks for "
            "<code>messages.sqlite3</code> and <code>golded.toml</code> "
            "in the current directory.</p>"
            + code_pane(
                "first-run-code",
                "open a base",
                "golded --database messages.sqlite3\n",
            )
            + '<p>To open areas across bases, use <a href="config.html#areadef">'
            "an AREADEF configuration</a>.</p>"
            "<p>The splash screen counts down from "
            f"{DEFAULT_SPLASH_SECONDS} (<code>splash_seconds</code> in "
            '<a href="config.html">golded.toml</a>'
            "); any key skips it. "
            "Pick an area with <code>↑</code> <code>↓</code> and "
            "<code>Enter</code>, open a message, and step with <code>←</code> "
            "<code>→</code>. <code>Esc</code> goes back one screen and quits "
            "from the area list. Set your name and address in "
            '<a href="config.html">golded.toml</a> before you write.</p>',
        ),
        (
            "manual",
            "02",
            "This manual",
            f'<ul class="contract-list">{pages}</ul>'
            "<p>Storage comes from the GoldED for Python libraries "
            "<code>golded-ftn</code> and <code>golded-ftn-sqlite</code>; their "
            f'<a href="{LIBRARY_DOCS}">library docs</a> describe the format.</p>',
        ),
    ]
    return shell(
        "index.html",
        "golded · GoldED message reader",
        "golded reads and writes FidoNet echomail and netmail stored in SQLite, "
        "in a terminal UI modelled on GoldED.",
        "Old echomail. New terminal.",
        "golded",
        "A message reader for the terminal.",
        "Read and write FidoNet echomail and netmail stored in SQLite. Area list, "
        "message list, thread tree, quoting replies, two DOS-era themes.",
        sections,
    )


def database_page() -> str:
    sections = [
        (
            "what",
            "00",
            "What golded opens",
            "<p>A SQLite message base is one file in the "
            "<code>golded-ftn-sqlite</code> format. It holds one or more areas; "
            "each area is echomail or netmail and has a code (<code>GENERAL</code>) "
            "and a display name. <code>golded</code> lists the areas, reads their "
            "messages and appends the messages you write. It does not delete, edit "
            "or toss messages.</p>"
            '<p>For JAM bases, see <a href="config.html#areadef">AREADEF configuration</a>.</p>'
            "<p>Close the base in other programs while <code>golded</code> writes "
            "to it. A read-only file can still be read; saving then fails with a "
            "message in the status bar, and the draft stays open.</p>",
        ),
        (
            "ftnt",
            "01",
            "Make a base with ftnt",
            "<p><code>ftnt</code> from "
            f'<a href="{FTNT_PYPI}">golded-ftn-tools</a> 1.2.0 creates a base with '
            "one area and appends messages from JSON:</p>"
            + code_pane(
                "ftnt-create",
                "create a base with one echomail area",
                "uvx --from golded-ftn-tools==1.2.0 ftnt create messages.sqlite3 \\\n"
                "  --format sqlite --area GENERAL --area-name 'General chat' "
                "--origin 2:236/777\n",
            )
            + code_pane(
                "ftnt-write",
                "append one message",
                'echo \'{"from_name":"Alice","to_name":"All","subject":"Hello",'
                '"body_text":"First post.\\n","posted_at":"2026-11-14T10:00:00"}\' \\\n'
                "  | uvx --from golded-ftn-tools==1.2.0 ftnt write messages.sqlite3 "
                "--format sqlite\n",
            )
            + "<p><code>--kind netmail</code> makes a netmail area instead. "
            "Then open it with <code>golded --database messages.sqlite3</code>.</p>",
        ),
        (
            "demo",
            "02",
            "Demo base for contributors",
            "<p>A checkout has <code>scripts/seed_demo.py</code>, which builds the "
            "base the tests and screenshots use: six areas covering an empty area, "
            "one message, a gap in message numbers, a long message, a thread and "
            "netmail. Its Faker seed is fixed, so the content is the same every "
            "time.</p>"
            + code_pane(
                "demo-seed",
                "in a checkout",
                "uv sync\nuv run python scripts/seed_demo.py\nuv run golded\n",
            )
            + '<p class="note"><strong>It deletes first.</strong> The seeder '
            "removes <code>messages.sqlite3</code> and its <code>-wal</code> and "
            "<code>-shm</code> files before writing. Do not run it next to a base "
            "you want to keep.</p>",
        ),
        (
            "errors",
            "03",
            "When it will not open",
            "<p>Startup problems print one line on stderr and exit with status 1.</p>"
            + table(
                ("Situation", "Message"),
                [
                    (
                        "No file at the path",
                        "<code>Database not found: PATH</code>, then a hint",
                    ),
                    (
                        "Not an SQLite file",
                        "<code>Cannot open database PATH: file is not a database</code>",
                    ),
                    (
                        "SQLite, but another schema or version",
                        "<code>Cannot open database PATH: not a supported "
                        "golded-ftn-sqlite database</code>",
                    ),
                    (
                        "Directory not writable",
                        "<code>Cannot open database PATH: attempt to write a "
                        "readonly database</code>",
                    ),
                ],
            ),
        ),
    ]
    return shell(
        "database.html",
        "Message bases · golded",
        "The SQLite message base golded opens, and how to create one.",
        "One file. Many areas.",
        "golded --database PATH",
        "Message bases.",
        "What a base is, how to make one with ftnt, and the demo base for "
        "working on golded itself.",
        sections,
    )


def config_page() -> str:
    example = (ROOT / "golded.toml.example").read_text(encoding="utf-8")
    sections = [
        (
            "file",
            "00",
            "golded.toml",
            "<p>TOML in the current directory, or the path given with "
            "<code>--config</code>. A missing file means defaults. Every field is "
            "optional.</p>"
            + code_pane("config-example", "golded.toml.example", example),
        ),
        (
            "fields",
            "01",
            "Fields",
            table(
                ("Field", "Default", "Meaning"),
                [
                    (
                        "<code>from_name</code>",
                        "empty",
                        "Your name, filled in when you write or reply. Saving needs a From name.",
                    ),
                    (
                        "<code>from_address</code>",
                        "none",
                        "Your FTN address, such as <code>2:236/777</code>. Used in "
                        "From and the Origin line.",
                    ),
                    (
                        "<code>database</code>",
                        "<code>messages.sqlite3</code>",
                        "The message base to open.",
                    ),
                    (
                        "<code>origin</code>",
                        "<code>Where we're going, we don't need roads.</code>",
                        "Text of the <code> * Origin:</code> line below the tearline.",
                    ),
                    (
                        "<code>theme</code>",
                        "<code>dark</code>",
                        "<code>dark</code> or <code>light</code>.",
                    ),
                    (
                        "<code>threaded_list</code>",
                        "<code>false</code>",
                        "Start the message list as a thread tree. A TOML boolean; "
                        "<code>t</code> toggles it in the app.",
                    ),
                    (
                        "<code>splash_seconds</code>",
                        f"<code>{DEFAULT_SPLASH_SECONDS}</code>",
                        "How long the splash screen counts down. A whole number; "
                        "<code>0</code> skips the splash.",
                    ),
                ],
            ),
        ),
        (
            "options",
            "02",
            "Command-line options",
            "<p>Options override the file.</p>"
            + table(
                ("Option", "Default", "Meaning"),
                [
                    (
                        "<code>--config PATH</code>",
                        "<code>golded.toml</code>",
                        "User config file",
                    ),
                    (
                        "<code>--database PATH</code>",
                        "from config, else <code>messages.sqlite3</code>",
                        "SQLite message base",
                    ),
                    (
                        "<code>--area-config PATH</code>",
                        "none",
                        "Read <a href='#areadef'>AREADEF entries</a> instead of opening one base.",
                    ),
                    (
                        "<code>--theme NAME</code>",
                        "from config, else <code>dark</code>",
                        "<code>dark</code> or <code>light</code>",
                    ),
                ],
            ),
        ),
        (
            "areadef",
            "03",
            "Classic area configuration",
            "<p>Run <code>golded --area-config golded.cfg</code> to list areas from "
            "existing SQLite and JAM bases in configuration order. "
            "This option replaces the TOML <code>database</code> setting and "
            "cannot be combined with <code>--database</code>. "
            "Keep identity, origin and display preferences in <code>golded.toml</code>.</p>"
            + code_pane(
                "areadef-example",
                "golded.cfg",
                'AREADEF GENERAL "General discussion" A Echo SQLite "bases/echo.sqlite3" . ()\n'
                'AREADEF NETMAIL "Private mail" #117 Net SQLite bases/mail.sqlite3 . ()\n'
                'AREADEF UNIX "UNIX discussion" A Echo JAM bases/UNIX . ()\n',
            )
            + "<p>Each AREADEF line gives the echo ID, quoted description, group, "
            "type, format and path. The group is a letter A–Z, 0, or #1–#999. "
            "Use <code>Echo</code> or <code>Net</code>. For SQLite, the type and echo ID "
            "must match an existing area. Echo IDs are matched without regard to ASCII case "
            "and must be unique in the configuration. Paths are relative to the configuration file "
            "unless absolute. Save the file as UTF-8.</p>"
            "<p><code>SQLite</code> is a GoldED.py extension. "
            "For <code>JAM</code>, use the base filename without the extension. "
            "Each JAM base represents one area and needs its existing "
            "<code>.JHR</code>, <code>.JDT</code> and <code>.JDX</code> files. "
            "Suffixes may be lowercase. GoldED checks the base on startup and reports "
            "invalid records. It uses the declared charset when reading, falls back to "
            "CP850, and writes in CP850. Characters outside CP850 stop the save and "
            "leave the draft open. Keep the base closed in other programs while using "
            "it here. A read-only base supports browsing.</p>"
            "<p><code>JAMREAD strict</code> sets the global JAM read mode. "
            "Strict is also the built-in default. Use <code>JAMREAD lenient</code> "
            "to change the default for all JAM areas, or "
            "<code>JAMREAD UNIX lenient</code> to override it for the UNIX area. "
            "An area override takes precedence regardless of directive order. "
            "Echo IDs in overrides use the same matching rules as AREADEF.</p>"
            "<p>Lenient mode keeps recoverable records and can skip invalid records "
            "or stop at an ambiguous index entry. Highlight the area to see counts "
            "of recovered deviations, skipped records and stopped traversals in the "
            "status bar. A stopped traversal may show only part of the base. "
            "JAM writing still validates the entire base strictly. If that check "
            "fails, the composer shows the error and keeps the draft open.</p>"
            "<p>The optional classic tail <code>aka (attrs) [origin]</code> "
            "and group are accepted without applying area-specific settings. "
            "Semicolons outside quoted fields start comments. Other directives, "
            "including <code>INCLUDE</code> and <code>AREAFILE</code>, are ignored. "
            "Use literal paths on the current system.</p>",
        ),
        (
            "errors",
            "04",
            "Invalid values",
            "<p>A config <code>golded</code> cannot use stops it at startup with "
            "<code>Cannot read config PATH: …</code> and exit status 1: malformed "
            "TOML, an invalid <code>from_address</code>, an unknown "
            "<code>theme</code>, a <code>threaded_list</code> that is not "
            '<code>true</code> or <code>false</code> (<code>"no"</code> is a '
            "string, and an error), or a <code>splash_seconds</code> that is "
            "not a whole number of 0 or more.</p>",
        ),
    ]
    return shell(
        "config.html",
        "Configuration · golded",
        "golded.toml fields and golded's command-line options.",
        "Your name. Your address.",
        "golded --config PATH",
        "Configuration.",
        "One TOML file and three options. Product name and version are fixed in the code.",
        sections,
    )


# Each row: keys as shown, what they do, and the bindings in the code that the
# row documents ("Class:key"). check_pages.py compares those with the code.
KEYS: tuple[tuple[str, str, str, tuple[tuple[str, str, tuple[str, ...]], ...]], ...] = (
    (
        "everywhere",
        "Everywhere",
        "Except where a screen uses the key itself: in the area list letters "
        "filter, and in the write screen they are text.",
        (
            ("q", "Quit", ("GoldED:q",)),
            ("Esc", "Back one screen; quits from the area list", ("GoldED:escape",)),
            ("F9", "Toggle the dark and light theme", ("GoldED:f9",)),
        ),
    ),
    (
        "splash",
        "Splash",
        "",
        (
            (
                "Any key",
                "Continue to the area list (otherwise after "
                f"{DEFAULT_SPLASH_SECONDS} seconds, or <code>splash_seconds</code>)",
                (),
            ),
        ),
    ),
    (
        "area-list",
        "Area list",
        "",
        (
            ("↑ / ↓", "Move the cursor", ()),
            ("Enter", "Open the area", ()),
            ("Space", "Page down", ("AreaListScreen:space",)),
            ("Shift+Space", "Page up", ("AreaListScreen:shift+space",)),
            ("Letters", "Filter on area name or code; Backspace deletes", ()),
        ),
    ),
    (
        "message-list",
        "Message list",
        "",
        (
            ("↑ / ↓", "Move the cursor", ()),
            ("Enter", "Open the message", ()),
            ("w", "Write a new message", ("MessageListScreen:w",)),
            ("t", "Toggle flat list and thread tree", ("MessageListScreen:t",)),
            ("Esc", "Back to the area list", ("MessageListScreen:escape",)),
            ("Space", "Page down", ("MessageListScreen:space",)),
            ("Shift+Space", "Page up", ("MessageListScreen:shift+space",)),
        ),
    ),
    (
        "message-view",
        "Message view",
        "",
        (
            ("→", "Next message", ("MessageViewScreen:right",)),
            ("←", "Previous message", ("MessageViewScreen:left",)),
            (
                "Shift+→",
                "Next message with the same subject",
                ("MessageViewScreen:shift+right",),
            ),
            (
                "Shift+←",
                "Previous message with the same subject",
                ("MessageViewScreen:shift+left",),
            ),
            ("Space", "Page down in the body", ("MessageViewScreen:space",)),
            ("Shift+Space", "Page up in the body", ("MessageViewScreen:shift+space",)),
            (
                "m",
                "Mojibake repair on or off (display only; the base is not changed)",
                ("MessageViewScreen:m",),
            ),
            ("w", "Write a new message", ("MessageViewScreen:w",)),
            (
                "r",
                "Reply, quoting the body as shown (with repair if m is on)",
                ("MessageViewScreen:r",),
            ),
            ("Esc", "Back to the message list", ("MessageViewScreen:escape",)),
        ),
    ),
    (
        "write",
        "Write and reply",
        "A new echomail message is addressed to All. Netmail needs the "
        "recipient's FTN address in the To address field before it saves. A "
        "reply starts with Hello and the author's first name, then the quoted "
        "body with their initials (Alice Bob gives AB>), without the tearline and "
        "Origin. Cmd+S reaches the app only in terminals that pass it on; F2 and "
        "Ctrl+S always work.",
        (
            (
                "F2 / Ctrl+S / Cmd+S",
                "Save the message",
                (
                    "WriteMessageScreen:f2",
                    "WriteMessageScreen:ctrl+s",
                    "WriteMessageScreen:super+s",
                ),
            ),
            (
                "↑ / ↓",
                "Move between From, To, Subj and the body; ↑ on the body's top "
                "line goes to Subj",
                ("WriteMessageScreen:up", "WriteMessageScreen:down"),
            ),
            (
                "Esc",
                "Cancel; asks before discarding the draft",
                ("WriteMessageScreen:escape",),
            ),
        ),
    ),
    (
        "discard",
        "Discard dialog",
        "",
        (
            ("y", "Discard the draft", ("DiscardDialog:y",)),
            ("n / Esc", "Keep writing", ("DiscardDialog:n", "DiscardDialog:escape")),
        ),
    ),
)


def keys_page() -> str:
    sections: list[Section] = []
    for number, (slug, title, note, rows) in enumerate(KEYS):
        cells = []
        for keys, action, bindings in rows:
            shown = " ".join(f"<kbd>{esc(part)}</kbd>" for part in keys.split(" / "))
            marker = f' data-bindings="{esc(" ".join(bindings))}"' if bindings else ""
            cells.append((f"<span{marker}>{shown}</span>", esc(action)))
        body = (f"<p>{esc(note)}</p>" if note else "") + table(("Key", "Action"), cells)
        sections.append((slug, f"{number:02d}", title, body))
    return shell(
        "keys.html",
        "Keys · golded",
        "Every golded key binding, screen by screen.",
        "No mouse needed. Mostly.",
        "golded",
        "Keys.",
        "Every key, screen by screen. The list is checked against the bindings "
        "in the code.",
        sections,
    )


SCREEN_TEXT = (
    (
        "splash",
        "Splash",
        "Product, version and licence, with a countdown. Any key continues.",
    ),
    (
        "area-list",
        "Area list",
        "Areas in the base with their message counts. Letters filter the list.",
    ),
    (
        "message-list",
        "Message list",
        "The THREADED demo area as a thread tree (<code>t</code>). The pagebar in "
        "the right border shows the position.",
    ),
    (
        "message-view",
        "Message view",
        "Header with message number, From, To and Subj, then the body. The status "
        "bar shows how many messages are left.",
    ),
    (
        "reply",
        "Reply",
        "<code>r</code> opens a draft with the greeting and the quoted body. "
        "<code>F2</code> saves it.",
    ),
)


def screens_page() -> str:
    sections: list[Section] = []
    for number, (slug, title, text) in enumerate(SCREEN_TEXT):
        figures = []
        for theme in ("dark", "light"):
            svg = (SCREENS / f"{slug}-{theme}.svg").read_text(encoding="utf-8")
            svg = svg.replace(
                '<svg class="rich-terminal"',
                f'<svg class="rich-terminal" role="img" aria-label="{esc(title)} screen, '
                f'{theme} theme"',
                1,
            )
            figures.append(
                f'<figure class="screen"><div class="screen-frame">{svg}</div>'
                f"<figcaption>{theme} theme</figcaption></figure>"
            )
        body = f"<p>{text}</p>" + f'<div class="screen-pair">{"".join(figures)}</div>'
        sections.append((slug, f"{number:02d}", title, body))
    return shell(
        "screens.html",
        "Screens · golded",
        "Screenshots of every golded screen in the dark and light themes.",
        "Blue screens. On purpose.",
        "golded --theme dark|light",
        "Screens.",
        "Each screen at 80×25 from the demo base, in both themes. Rendered by "
        "Textual from the running app, not drawn by hand.",
        sections,
    )


def main() -> None:
    pages = {
        "index.html": index_page(),
        "database.html": database_page(),
        "config.html": config_page(),
        "keys.html": keys_page(),
        "screens.html": screens_page(),
    }
    SITE.mkdir(exist_ok=True)
    for name, text in pages.items():
        (SITE / name).write_text(text, encoding="utf-8")
    print(f"Wrote {len(pages)} manual pages to site/.")


if __name__ == "__main__":
    main()
