"""User settings for writing and startup."""

import tomllib
from pathlib import Path

from golded_ftn import FtnAddress

from golded.data.area_config import ConfiguredArea, parse_toml_areas
from golded.logic.tear_origin import DEFAULT_ORIGIN

THEME_NAMES = ("dark", "light")
DEFAULT_THEME = "dark"
DEFAULT_THREADED_LIST = False
DEFAULT_SPLASH_SECONDS = 10


class UserConfig:
    def __init__(
        self,
        from_name: str = "",
        from_address: FtnAddress | None = None,
        database: str = "",
        origin: str = DEFAULT_ORIGIN,
        theme: str = DEFAULT_THEME,
        threaded_list: bool = DEFAULT_THREADED_LIST,
        splash_seconds: int = DEFAULT_SPLASH_SECONDS,
        areas: tuple[ConfiguredArea, ...] = (),
    ) -> None:
        self.from_name = from_name
        self.from_address = from_address
        self.database = database
        self.origin = DEFAULT_ORIGIN if origin.strip() == "" else origin
        self.theme = theme if theme in THEME_NAMES else DEFAULT_THEME
        self.threaded_list = bool(threaded_list)
        self.splash_seconds = splash_seconds
        self.areas = areas


def load_user_config(path: str | Path, *, load_areas: bool = True) -> UserConfig:
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
    splash_seconds = data.get("splash_seconds", DEFAULT_SPLASH_SECONDS)
    from_address = None

    if theme not in THEME_NAMES:
        raise ValueError(
            f"theme must be one of {', '.join(THEME_NAMES)}, not {theme!r}"
        )

    if not isinstance(threaded_list, bool):
        raise ValueError(f"threaded_list must be true or false, not {threaded_list!r}")

    # TOML booleans load as bool, which is a subclass of int.
    if type(splash_seconds) is not int or splash_seconds < 0:
        raise ValueError(
            "splash_seconds must be a whole number of 0 or more, "
            f"not {splash_seconds!r}"
        )

    address_text = str(data.get("from_address", "")).strip()
    if address_text != "":
        from_address = FtnAddress.from_string(address_text)

    return UserConfig(
        from_name=from_name,
        from_address=from_address,
        database=database,
        origin=origin,
        theme=theme,
        threaded_list=threaded_list,
        splash_seconds=splash_seconds,
        areas=parse_toml_areas(data.get("areas", {}), data.get("jam", {}))
        if load_areas
        else (),
    )
