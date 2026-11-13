"""Optional display repair for damaged charset text."""

from golded_ftn import repair_mojibake
from rich.text import Text

def for_display(text: str, repair: bool) -> str:
    if not repair:
        return text

    return repair_mojibake(text).text

def literal_text(text: str) -> Text:
    return Text(text)
