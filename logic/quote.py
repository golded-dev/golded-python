"""Classic GoldED FL quote initials."""

def quote_initials(from_name: str) -> str:
    words = from_name.split()
    letters = []

    for word in words:
        for character in word:
            if character.isalpha():
                letters.append(character.upper())
                break

    if len(letters) == 0:
        return ""

    if len(letters) == 1:
        return letters[0]

    return letters[0] + letters[-1]

def _is_origin_line(line: str) -> bool:
    return line.startswith(" * Origin: ")

def _is_tearline_line(line: str) -> bool:
    return line.startswith("--- ")

def _trailing_tagline_start(lines: list[str]) -> int | None:
    index = len(lines) - 1

    while index >= 0 and lines[index].strip() == "":
        index -= 1

    if index < 0 or not _is_origin_line(lines[index]):
        return None

    tear_index = index - 1
    while tear_index >= 0 and lines[tear_index].strip() == "":
        tear_index -= 1

    if tear_index < 0 or not _is_tearline_line(lines[tear_index]):
        return None

    return tear_index

def body_without_tearline(body_text: str) -> str:
    lines = body_text.splitlines()
    start = _trailing_tagline_start(lines)

    if start is None:
        return body_text

    return "\n".join(lines[:start])

def split_body_at_tagline(body_text: str) -> tuple[str, str]:
    lines = body_text.splitlines()
    start = _trailing_tagline_start(lines)

    if start is None:
        return body_text, ""

    return "\n".join(lines[:start]), "\n".join(lines[start:])

def has_golded_tagline(body_text: str) -> bool:
    lines = body_text.splitlines()
    start = _trailing_tagline_start(lines)

    if start is not None:
        return lines[start].startswith("--- GoldED")

    index = len(lines) - 1
    while index >= 0 and lines[index].strip() == "":
        index -= 1

    if index < 0:
        return False

    return lines[index].startswith("--- GoldED")

def quote_body(from_name: str, body_text: str) -> str:
    initials = quote_initials(from_name)
    main = body_without_tearline(body_text)
    lines = []

    for line in main.splitlines():
        if initials == "":
            if line == "":
                lines.append(">")
            else:
                lines.append("> " + line)
        else:
            if line == "":
                lines.append(initials + ">")
            else:
                lines.append(initials + "> " + line)

    return "\n".join(lines) + "\n"

def first_name(full_name: str) -> str:
    words = full_name.split()
    if len(words) == 0:
        return ""

    return words[0]

def reply_intro(from_name: str, body_for_quote: str) -> str:
    name = first_name(from_name)
    if name == "":
        greeting = "Hello"
    else:
        greeting = "Hello " + name

    quoted = quote_body(from_name, body_for_quote)

    return greeting + "\n\n" + quoted
