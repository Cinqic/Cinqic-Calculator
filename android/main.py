"""Kivy Android frontend entry point for Cinqic Calculator.

This is a separate, independent frontend from cinqic_calculator.ui (the
Tkinter desktop app), which it does not import, modify, or otherwise
affect. It reuses the platform-independent core (calculator.py,
evaluator.py, financial.py, conversions.py, history.py, settings.py,
storage.py, constants.py) unchanged.

Local-module imports here (``logic``, ``android_constants``, ``screens.*``)
are intentionally flat, not ``android.logic`` etc. On an Android device,
python-for-android runs this file with this directory itself as the app
root (see buildozer.spec's ``source.dir``), and Python also puts a
directly-run script's own directory first on sys.path - so flat imports
work identically whether this runs on-device or via
``python android/main.py`` for local desktop iteration. Only
tests/test_android_glue.py (run from the repo root under pytest) addresses
these modules via the dotted ``android.<module>`` path.
"""

from __future__ import annotations

import os
import sys

# Make the shared cinqic_calculator core importable. On a real Android
# build, the CI build step is expected to have copied/symlinked
# src/cinqic_calculator next to this file (see android/README.md) since
# python-for-android only bundles files under buildozer.spec's source.dir.
# For local desktop development (this repo, running `python android/main.py`
# on a machine with Kivy installed), cinqic_calculator is instead reachable
# via ../src, so fall back to adding that to sys.path.
try:
    import cinqic_calculator  # noqa: F401
except ImportError:
    _repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _src_dir = os.path.join(_repo_root, "src")
    if os.path.isdir(_src_dir) and _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import NoTransition, ScreenManager

from cinqic_calculator import constants
from cinqic_calculator.history import History
from cinqic_calculator.settings import Settings

from android_constants import ANDROID_APP_VERSION
from logic import ScreenInputRouter, resolve_data_dir
from screens.about_screen import AboutScreen
from screens.calculator_screen import CalculatorScreen
from screens.convert_screen import ConvertScreen
from screens.financial_screen import FinancialScreen
from screens.history_screen import HistoryScreen
from screens.settings_screen import SettingsScreen

_BACK_KEYCODE = 27  # Android hardware/software back button

# Each screen's .kv lives under android/kv/ instead of relying on Kivy's
# automatic "same name as the App class, lowercased" kv file lookup, purely
# for readability (one small file per screen). They must be loaded before
# the matching Screen subclasses are instantiated below, since kv rules are
# applied to widgets at creation time, not retroactively.
_KV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv")
for _kv_filename in ("calculator.kv", "convert.kv", "financial.kv", "history.kv", "settings.kv", "about.kv"):
    Builder.load_file(os.path.join(_KV_DIR, _kv_filename))


class CinqicCalculatorApp(App):
    """Root Kivy application. Package identity (com.cinqic.calculator),
    version (1.0.0), and versionCode (1) are set in buildozer.spec, not
    here - this class only sets the in-app window title.
    """

    def build(self):
        self.title = constants.APP_NAME
        self.android_version = ANDROID_APP_VERSION
        self.input_router = ScreenInputRouter()

        data_dir = resolve_data_dir(self.user_data_dir)
        self.settings = Settings(Settings.default_path(data_dir))
        self.history = History(
            History.default_path(data_dir),
            enabled=self.settings.get("save_history", True),
        )

        theme = self.settings.get("theme", "dark")
        self.colors = constants.get_colors(theme if theme in ("dark", "light") else "dark")
        Window.clearcolor = _hex_to_rgba(self.colors["background"])

        self.screen_manager = ScreenManager(transition=NoTransition())
        self.screen_manager.add_widget(CalculatorScreen(name="calculator"))
        self.screen_manager.add_widget(ConvertScreen(name="convert"))
        self.screen_manager.add_widget(FinancialScreen(name="financial"))
        self.screen_manager.add_widget(HistoryScreen(name="history"))
        self.screen_manager.add_widget(SettingsScreen(name="settings"))
        self.screen_manager.add_widget(AboutScreen(name="about"))

        self.screen_manager.current = "calculator"
        self.input_router.set_active("calculator")
        self.screen_manager.bind(current=self._on_screen_changed)

        Window.bind(on_keyboard=self._on_keyboard)

        return self.screen_manager

    def apply_theme(self, theme_name: str):
        """Re-apply colors after the Settings screen changes the theme."""
        self.colors = constants.get_colors(theme_name if theme_name in ("dark", "light") else "dark")
        Window.clearcolor = _hex_to_rgba(self.colors["background"])
        calculator_screen = self.screen_manager.get_screen("calculator")
        calculator_screen.background_color = _hex_to_rgba(self.colors["background"])

    def _on_screen_changed(self, _manager, screen_name):
        self.input_router.set_active(screen_name)

    def _on_keyboard(self, _window, key, *_args):
        # The hardware/software back button navigates to the Calculator
        # screen instead of exiting the app, unless already there. This is
        # the one place a Window-level (i.e. global, not screen-scoped)
        # binding exists, so it is guarded through input_router exactly as
        # described in logic.ScreenInputRouter's docstring: it only ever
        # acts based on which screen self.screen_manager reports as
        # current, never by reaching into a screen that isn't active.
        if key == _BACK_KEYCODE:
            if self.input_router.active_screen_name != "calculator":
                self.screen_manager.current = "calculator"
                return True
            return False
        return False

    def on_stop(self):
        self.settings.save()


def _hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, 1)


if __name__ == "__main__":
    CinqicCalculatorApp().run()
