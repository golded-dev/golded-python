"""Classic FTN tearline and Origin footer."""

from golded_ftn import FtnAddress

from golded.logic.quote import body_without_tearline
from golded.logic.version import PRODUCT

DEFAULT_ORIGIN = "Where we're going, we don't need roads."

def tear_origin_block(
    origin: str,
    from_address: FtnAddress | None = None,
) -> str:
    text = origin.strip()
    if text == "":
        text = DEFAULT_ORIGIN

    if from_address is None:
        origin_line = f" * Origin: {text}"
    else:
        origin_line = f" * Origin: {text} ({from_address})"

    return f"--- {PRODUCT}\n{origin_line}\n"

def with_tear_origin(
    body_text: str,
    origin: str,
    from_address: FtnAddress | None = None,
) -> str:
    main = body_without_tearline(body_text).rstrip()
    footer = tear_origin_block(origin, from_address)

    if main == "":
        return footer

    return main + "\n\n" + footer
