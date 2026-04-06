from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = "SundayCityGroups"


def get_app_data_dir() -> Path:
    base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base_dir:
        return Path(base_dir) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME.lower()}"


def get_database_path() -> Path:
    return get_app_data_dir() / "data" / "clan_manager.db"
