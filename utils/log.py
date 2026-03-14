"""Lightweight logging to file in addon folder."""

from __future__ import annotations

import os
import traceback
from datetime import datetime
from typing import Any

LOG_ENABLED = True
LOG_FILENAME = "myaddon.log"


def _log_path() -> str:
    addon_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(addon_root, LOG_FILENAME)


def _write(level: str, message: str) -> None:
    if not LOG_ENABLED:
        return
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {level}: {message}\n"
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Last resort: drop errors silently to avoid breaking addon.
        pass


def log_info(message: str) -> None:
    _write("INFO", message)


def log_warn(message: str) -> None:
    _write("WARN", message)


def log_error(message: str, exc: BaseException | None = None) -> None:
    if exc is None:
        _write("ERROR", message)
        return
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    _write("ERROR", f"{message}\n{tb}")
