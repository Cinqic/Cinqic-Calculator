"""History screen: scrollable list of past calculations, tap-to-reuse,
per-row delete, and clear-all. Reads/writes only through the shared
History instance owned by the App - never keeps its own copy of entries
beyond what it needs to render the current list.
"""

from __future__ import annotations

from kivy.app import App
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class HistoryScreen(Screen):
    rows_data = ListProperty([])
    status_text = StringProperty("")

    def on_pre_enter(self, *_args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        self.rows_data = list(enumerate(app.history.entries))
        self.status_text = "" if app.settings.get("save_history", True) else "History saving is currently off in Settings."
        self._rebuild_rows()

    def _rebuild_rows(self):
        container = self.ids.rows_container
        container.clear_widgets()
        if not self.rows_data:
            container.add_widget(Label(text="No history yet.", size_hint_y=None, height="40dp"))
            return
        # Show most recent first.
        for index, entry in reversed(self.rows_data):
            container.add_widget(self._build_row(index, entry))

    def _build_row(self, index: int, entry: dict) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height="56dp", spacing="6dp")
        summary = f"{entry['expression']} = {entry['result']}  ({entry['timestamp']})"
        reuse_button = Button(text=summary)
        reuse_button.bind(on_release=lambda _btn, i=index: self.reuse_entry(i))
        delete_button = Button(text="Delete", size_hint_x=0.25)
        delete_button.bind(on_release=lambda _btn, i=index: self.delete_entry(i))
        row.add_widget(reuse_button)
        row.add_widget(delete_button)
        return row

    # -- Actions --------------------------------------------------------
    def reuse_entry(self, index: int):
        app = App.get_running_app()
        entries = app.history.entries
        if not (0 <= index < len(entries)):
            return
        result = entries[index]["result"]
        calculator_screen = app.screen_manager.get_screen("calculator")
        calculator_screen.calc.display = result
        calculator_screen.calc.start_fresh = True
        calculator_screen._refresh()
        app.screen_manager.current = "calculator"

    def delete_entry(self, index: int):
        app = App.get_running_app()
        app.history.delete_at(index)
        self.refresh()

    def clear_all(self):
        app = App.get_running_app()
        app.history.clear()
        self.refresh()
