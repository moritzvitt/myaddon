from __future__ import annotations

from aqt import mw


ADDON_MODULE = __package__ or __name__.split(".", 1)[0]


def get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(ADDON_MODULE) or {}
    if "deck" not in config or not str(config.get("deck") or "").strip():
        config["deck"] = "migaku"
    if "preview_query" not in config or not str(config.get("preview_query") or "").strip():
        config[
            "preview_query"
        ] = "deck:JP -is:suspended -is:buried is:new -flag:3 -flag:2 -flag:4 -flag:1 -flag:6 -tag:marked"
    if "preview_tag" not in config or not str(config.get("preview_tag") or "").strip():
        config["preview_tag"] = "preview"
    if "preview_limit" not in config:
        config["preview_limit"] = 200
    return config


def save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(ADDON_MODULE, config)
