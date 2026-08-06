"""Shared constants: app identity, paths, and color palette."""

import os

APP_NAME = "Cinqic Calculator"
APP_VERSION = "1.0.1"
APP_ID = "com.cinqic.calculator"

MAX_HISTORY_ENTRIES = 200


def data_dir(override_base: str | None = None) -> str:
    """Return the per-user application data directory, creating it if needed.

    ``override_base`` lets a platform frontend supply its own private storage
    root (e.g. Android's ``App.user_data_dir``) instead of the Windows
    ``LOCALAPPDATA``/home fallback used by the desktop app.
    """
    if override_base is not None:
        os.makedirs(override_base, exist_ok=True)
        return override_base
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


def detect_system_theme() -> str:
    """Best-effort Windows light/dark detection. Falls back to 'dark'."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except OSError:
        return "dark"


def resolve_theme(theme_name: str) -> str:
    if theme_name == "system":
        return detect_system_theme()
    if theme_name not in ("dark", "light"):
        return "dark"
    return theme_name


def get_colors(theme_name: str) -> dict:
    """Return a color dict for 'dark' or 'light' (call resolve_theme first)."""
    if theme_name == "light":
        return {
            "background": LIGHT_COLOR_BACKGROUND,
            "panel": LIGHT_COLOR_PANEL,
            "panel_alt": LIGHT_COLOR_PANEL_ALT,
            "text_primary": LIGHT_COLOR_TEXT_PRIMARY,
            "text_secondary": LIGHT_COLOR_TEXT_SECONDARY,
            "accent": LIGHT_COLOR_ACCENT,
            "accent_active": LIGHT_COLOR_ACCENT_ACTIVE,
            "border": LIGHT_COLOR_BORDER,
            "error": LIGHT_COLOR_ERROR,
        }
    return {
        "background": COLOR_BACKGROUND,
        "panel": COLOR_PANEL,
        "panel_alt": COLOR_PANEL_ALT,
        "text_primary": COLOR_TEXT_PRIMARY,
        "text_secondary": COLOR_TEXT_SECONDARY,
        "accent": COLOR_ACCENT,
        "accent_active": COLOR_ACCENT_ACTIVE,
        "border": COLOR_BORDER,
        "error": COLOR_ERROR,
    }
