"""Settings screen: theme, history, memory, motion, and haptics.

Theme is dark/light only, with no "system" option: the shared
``detect_system_theme()`` reads a Windows registry key or a freedesktop
``gsettings`` value, and neither exists on Android, so a "system" choice
here would silently mean "dark".

The persist_memory toggle's on/off semantics are delegated entirely to
android/logic.py's set_persist_memory(), which replicates the desktop
v1.0.1 fix (turning it off clears the stored memory value immediately,
rather than the pre-1.0.1 no-op behavior).
"""

from __future__ import annotations

from kivy.app import App
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.screenmanager import Screen

import haptics
from logic import set_persist_memory


class SettingsScreen(Screen):
    theme = StringProperty("dark")
    save_history_enabled = BooleanProperty(True)
    persist_memory_enabled = BooleanProperty(False)
    reduced_motion_enabled = BooleanProperty(False)
    haptics_setting_enabled = BooleanProperty(True)
    haptics_supported = BooleanProperty(False)
    haptics_note = StringProperty("")

    def on_pre_enter(self, *_args):
        app = App.get_running_app()
        theme = app.settings.get("theme", "dark")
        self.theme = theme if theme in ("dark", "light") else "dark"
        self.save_history_enabled = app.settings.get("save_history", True)
        self.persist_memory_enabled = app.settings.get("persist_memory", False)
        self.reduced_motion_enabled = app.settings.get("reduced_motion", False)
        self.haptics_setting_enabled = app.settings.get("haptics", True)
        # Report honestly rather than offering a switch that does nothing:
        # haptics need a real Android view, which desktop/CI runs don't have.
        self.haptics_supported = haptics.is_available()
        self.haptics_note = (
            "Uses Android's built-in key-press feedback. No extra permission is requested."
            if self.haptics_supported
            else "Haptic feedback is not available on this device."
        )

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

    def toggle_reduced_motion(self, enabled: bool):
        """Turn keypad and display animation off (or back on).

        Applied to the live calculator screen immediately, not just on the
        next visit, so the effect of the switch is visible right away.
        """
        app = App.get_running_app()
        self.reduced_motion_enabled = enabled
        app.settings.set("reduced_motion", bool(enabled))
        app.settings.save()
        calculator_screen = app.screen_manager.get_screen("calculator")
        calculator_screen.apply_motion_preference(bool(enabled))

    def toggle_haptics(self, enabled: bool):
        app = App.get_running_app()
        self.haptics_setting_enabled = enabled
        app.settings.set("haptics", bool(enabled))
        app.settings.save()
