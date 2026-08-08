"""Settings screen: theme (dark/light - no "system" option on Android,
since cinqic_calculator.constants.detect_system_theme() is Windows-only via
winreg), save_history toggle, and persist_memory toggle.

The persist_memory toggle's on/off semantics are delegated entirely to
android/logic.py's set_persist_memory(), which replicates the desktop
v1.0.1 fix (turning it off clears the stored memory value immediately,
rather than the pre-1.0.1 no-op behavior).
"""

from __future__ import annotations

from kivy.app import App
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import Screen

from logic import set_persist_memory


class SettingsScreen(Screen):
    theme = StringProperty("dark")
    save_history_enabled = BooleanProperty(True)
    persist_memory_enabled = BooleanProperty(False)

    def on_pre_enter(self, *_args):
        app = App.get_running_app()
        theme = app.settings.get("theme", "dark")
        self.theme = theme if theme in ("dark", "light") else "dark"
        self.save_history_enabled = app.settings.get("save_history", True)
        self.persist_memory_enabled = app.settings.get("persist_memory", False)

    def set_theme(self, theme_name: str):
        app = App.get_running_app()
        if theme_name not in ("dark", "light"):
            theme_name = "dark"
        self.theme = theme_name
        app.settings.set("theme", theme_name)
        app.settings.save()
        app.apply_theme(theme_name)

    def toggle_save_history(self, enabled: bool):
        app = App.get_running_app()
        self.save_history_enabled = enabled
        app.settings.set("save_history", enabled)
        app.settings.save()
        app.history.set_enabled(enabled)

    def toggle_persist_memory(self, enabled: bool):
        app = App.get_running_app()
        self.persist_memory_enabled = enabled
        set_persist_memory(app.settings, enabled)
