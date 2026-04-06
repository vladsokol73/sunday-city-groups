from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS"))
    else:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def get_app_icon_path() -> str | None:
    icon_path = resource_path("assets/amg.ico")
    return str(icon_path) if icon_path.exists() else None
