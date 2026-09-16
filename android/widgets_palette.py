"""The Android keypad's colour palette, as plain hex strings.

Deliberately free of any Kivy import so the contrast of every key can be
checked by ``tests/test_accessibility.py`` on a machine with no GUI toolkit
installed -- the same reason ``logic.py`` exists. ``widgets.py`` converts
these to the RGBA tuples Kivy wants.
"""

from __future__ import annotations

__all__ = ["KIND_COLORS_HEX", "DISABLED_ALPHA", "hex_to_rgba"]

#: kind -> (background, foreground). Every pair clears WCAG AA (4.5:1).
KIND_COLORS_HEX = {
    "number": ("#212121", "#FFFFFF"),
    "function": ("#171717", "#C7C7C7"),
    "operator": ("#1C2B1C", "#5CD45C"),
    "equals": ("#33CC33", "#050505"),
    "accent": ("#1C2B1C", "#5CD45C"),
}

#: Opacity applied to a disabled key. Low enough to read as unavailable,
#: high enough that the label does not vanish entirely.
DISABLED_ALPHA = 0.35


def hex_to_rgba(hex_color: str, alpha: float = 1.0):
    """Convert ``#rrggbb`` to the 0-1 RGBA tuple Kivy expects."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16) / 255.0,
        int(hex_color[2:4], 16) / 255.0,
        int(hex_color[4:6], 16) / 255.0,
        alpha,
    )
