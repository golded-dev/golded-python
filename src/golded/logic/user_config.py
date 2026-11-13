"""User settings for writing and startup."""

import tomllib
from pathlib import Path

from golded_ftn import FtnAddress

from golded.logic.tear_origin import DEFAULT_ORIGIN

THEME_NAMES = ("dark", "light")
DEFAULT_THEME = "dark"
DEFAULT_THREADED_LIST = False

class UserConfig:
    def __init__(
        self,
        from_name: str = "",
        from_address: FtnAddress | None = None,
        database: str = "",
        origin: str = DEFAULT_ORIGIN,
        theme: str = DEFAULT_THEME,
        threaded_list: bool = DEFAULT_THREADED_LIST,
    ) -> None:
        self.from_name = from_name
        self.from_address = from_address
        self.database = database
        self.origin = DEFAULT_ORIGIN if origin.strip() == "" else origin
        self.theme = theme if theme in THEME_NAMES else DEFAULT_THEME
        self.threaded_list = bool(threaded_list)

def load_user_config(path) -> UserConfig:
    config_path = Path(path)

    if not config_path.is_file():
        return UserConfig()

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    from_name = str(data.get("from_name", ""))
    database = str(data.get("database", ""))
    origin = str(data.get("origin", DEFAULT_ORIGIN))
    theme = str(data.get("theme", DEFAULT_THEME)).strip()
    threaded_list = data.get("threaded_list", DEFAULT_THREADED_LIST)
    from_address = None

    address_text = str(data.get("from_address", "")).strip()
    if address_text != "":
        from_address = FtnAddress.from_string(address_text)

    return UserConfig(
        from_name = from_name,
        from_address = from_address,
        database = database,
        origin = origin,
        theme = theme,
        threaded_list = bool(threaded_list),
    )
