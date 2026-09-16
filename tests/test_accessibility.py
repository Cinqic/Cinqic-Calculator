"""Accessibility guards that are cheap to check and easy to regress.

Colour contrast is the obvious one: it is invisible to a developer with good
eyesight on a good monitor, and a single palette tweak can quietly drop a
whole theme below the readable threshold. The light theme's accent really did
sit at 3.1:1 against the keypad before 1.1.0.
"""

import pytest

from cinqic_calculator.constants import contrast_ratio, get_colors, readable_text_on

#: WCAG 2.1 AA for normal-size text.
AA_NORMAL = 4.5

THEMES = ("dark", "light")


def text_pairs(colors):
    """(label, foreground, background) for every text/background combination."""
    accent_text = readable_text_on(colors["accent"])
    return [
        ("primary text on background", colors["text_primary"], colors["background"]),
        ("primary text on panel", colors["text_primary"], colors["panel"]),
        ("primary text on panel_alt", colors["text_primary"], colors["panel_alt"]),
        ("secondary text on background", colors["text_secondary"], colors["background"]),
        ("secondary text on panel", colors["text_secondary"], colors["panel"]),
        ("accent text on background", colors["accent"], colors["background"]),
        ("accent text on panel", colors["accent"], colors["panel"]),
        ("accent text on panel_alt", colors["accent"], colors["panel_alt"]),
        ("error text on background", colors["error"], colors["background"]),
        ("error text on panel", colors["error"], colors["panel"]),
        ("label on the accent fill", accent_text, colors["accent"]),
        ("label on the active accent fill", accent_text, colors["accent_active"]),
    ]


@pytest.mark.parametrize("theme", THEMES)
def test_every_text_colour_meets_wcag_aa(theme):
    colors = get_colors(theme)
    failures = []
    for label, foreground, background in text_pairs(colors):
        ratio = contrast_ratio(foreground, background)
        if ratio < AA_NORMAL:
            failures.append(f"{theme}: {label} is only {ratio:.2f}:1 (needs {AA_NORMAL}:1)")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("theme", THEMES)
def test_readable_text_picks_the_higher_contrast_option(theme):
    accent = get_colors(theme)["accent"]
    chosen = readable_text_on(accent)
    other = "#FFFFFF" if chosen == "#000000" else "#000000"
    assert contrast_ratio(chosen, accent) >= contrast_ratio(other, accent)


def test_contrast_ratio_endpoints():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("theme", THEMES)
def test_themes_are_visually_distinct_from_each_other(theme):
    """The panel must be distinguishable from the page behind it."""
    colors = get_colors(theme)
    assert contrast_ratio(colors["panel"], colors["background"]) > 1.0
    assert colors["border"] != colors["background"]


# ---------------------------------------------------------------------------
# Android keypad palette
# ---------------------------------------------------------------------------
def test_android_key_colours_meet_wcag_aa():
    """The Kivy keypad has its own palette and needs the same guarantee."""
    from android.widgets_palette import KIND_COLORS_HEX

    failures = []
    for kind, (background, foreground) in KIND_COLORS_HEX.items():
        ratio = contrast_ratio(foreground, background)
        if ratio < AA_NORMAL:
            failures.append(f"android {kind} key: {ratio:.2f}:1 (needs {AA_NORMAL}:1)")
    assert not failures, "\n".join(failures)


def test_android_disabled_keys_are_still_distinguishable():
    """A disabled key must read as disabled without becoming invisible."""
    from android.widgets_palette import DISABLED_ALPHA

    assert 0.2 <= DISABLED_ALPHA <= 0.6
