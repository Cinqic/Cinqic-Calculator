"""Shared constants: app identity, paths, and color palette."""

import os

APP_NAME = "Cinqic Calculator"
APP_VERSION = "1.0.0"
APP_ID = "com.cinqic.calculator"

MAX_HISTORY_ENTRIES = 200


def data_dir() -> str:
    """Return the per-user application data directory, creating it if needed."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "Cinqic", "Calculator")
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Dark "Juniper-inspired" color palette
# ---------------------------------------------------------------------------
COLOR_BACKGROUND = "#0A0A0A"
COLOR_PANEL = "#161616"
COLOR_PANEL_ALT = "#1E1E1E"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#A0A0A0"
COLOR_ACCENT = "#32CD32"
COLOR_ACCENT_ACTIVE = "#28A428"
COLOR_BORDER = "#2A2A2A"
COLOR_ERROR = "#FF6B6B"

LIGHT_COLOR_BACKGROUND = "#F5F5F5"
LIGHT_COLOR_PANEL = "#FFFFFF"
LIGHT_COLOR_PANEL_ALT = "#ECECEC"
LIGHT_COLOR_TEXT_PRIMARY = "#111111"
LIGHT_COLOR_TEXT_SECONDARY = "#5A5A5A"
LIGHT_COLOR_ACCENT = "#219A21"
LIGHT_COLOR_ACCENT_ACTIVE = "#1B7E1B"
LIGHT_COLOR_BORDER = "#D6D6D6"
LIGHT_COLOR_ERROR = "#C62828"
