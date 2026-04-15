from __future__ import annotations

from aqt import mw

GREEN_FLAG_SYNONYM_MODE_KEY = "green_flag_synonym_mode"
GREEN_FLAG_SYNONYM_MODE_FIRST = "first"
GREEN_FLAG_SYNONYM_MODE_FIRST_TWO = "first_two"
GREEN_FLAG_SYNONYM_MODE_ALL = "all"
DEFAULT_CONFIG = {
    GREEN_FLAG_SYNONYM_MODE_KEY: GREEN_FLAG_SYNONYM_MODE_FIRST_TWO,
}
SYNONYM_MODE_LABELS = {
    GREEN_FLAG_SYNONYM_MODE_FIRST: "First synonym only",
    GREEN_FLAG_SYNONYM_MODE_FIRST_TWO: "First two synonyms",
    GREEN_FLAG_SYNONYM_MODE_ALL: "All available synonyms",
}


def load_config() -> dict[str, str]:
    addon_name = __name__.split(".", 1)[0]
    raw = mw.addonManager.getConfig(addon_name) or {}
    mode = raw.get(GREEN_FLAG_SYNONYM_MODE_KEY)
    if mode not in SYNONYM_MODE_LABELS:
        mode = DEFAULT_CONFIG[GREEN_FLAG_SYNONYM_MODE_KEY]
    return {
        GREEN_FLAG_SYNONYM_MODE_KEY: mode,
    }


def save_config(config: dict[str, str]) -> None:
    addon_name = __name__.split(".", 1)[0]
    mw.addonManager.writeConfig(addon_name, config)
