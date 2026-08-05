"""Interface smoke tests: import every UI module, build/close the main window,
and check keyboard/button callbacks don't raise. Skipped when no display is
available (e.g. a headless CI runner without Xvfb) so it never hangs CI.
"""

import os

import pytest

tk = pytest.importorskip("tkinter")


def _display_available() -> bool:
    if os.name == "nt":
        try:
            root = tk.Tk()
            root.destroy()
            return True
        except tk.TclError:
            return False
    return bool(os.environ.get("DISPLAY"))


pytestmark = pytest.mark.skipif(not _display_available(), reason="No display available for GUI smoke test")


def test_import_all_ui_modules():
    import cinqic_calculator.ui.about_view  # noqa: F401
    import cinqic_calculator.ui.calculator_view  # noqa: F401
    import cinqic_calculator.ui.components  # noqa: F401
    import cinqic_calculator.ui.converter_view  # noqa: F401
    import cinqic_calculator.ui.financial_view  # noqa: F401
    import cinqic_calculator.ui.history_view  # noqa: F401
    import cinqic_calculator.ui.main_window  # noqa: F401
    import cinqic_calculator.ui.settings_view  # noqa: F401


def test_main_window_creates_and_closes(tmp_path):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    settings = Settings(str(tmp_path / "settings.json"))
    history = History(str(tmp_path / "history.json"))

    window = MainWindow(settings, history)
    try:
        window.update()
        for name in window.views:
            window.show_view(name)
            window.update()
    finally:
        window.destroy()


def test_calculator_view_button_and_keyboard_callbacks(tmp_path):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    settings = Settings(str(tmp_path / "settings.json"))
    history = History(str(tmp_path / "history.json"))
    window = MainWindow(settings, history)
    try:
        calc_view = window.views["Calculator"]
        calc_view._on_button("5")
        calc_view._on_button("+")
        calc_view._on_button("3")
        calc_view._on_button("=")
        window.update()
        assert calc_view.calc.display == "8"

        calc_view.copy_result()
        calc_view._backspace()
        calc_view.toggle_scientific()
        calc_view._apply_scientific("square")
        window.update()
    finally:
        window.destroy()


def test_history_view_reuse_and_delete(tmp_path):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    settings = Settings(str(tmp_path / "settings.json"))
    history = History(str(tmp_path / "history.json"))
    history.add("2 + 2", "4", "2026-01-01T00:00:00")
    window = MainWindow(settings, history)
    try:
        window.show_view("History")
        history_view = window.views["History"]
        history_view.refresh()
        window.update()
        history_view.tree.selection_set("0")
        history_view._copy_selected()
        history_view._reuse_selected()
        window.update()
        assert window.views["Calculator"].calc.display == "4"
    finally:
        window.destroy()


def test_settings_view_toggles(tmp_path):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    settings = Settings(str(tmp_path / "settings.json"))
    history = History(str(tmp_path / "history.json"))
    window = MainWindow(settings, history)
    try:
        window.show_view("Settings")
        settings_view = window.views["Settings"]
        settings_view.save_history_var.set(False)
        settings_view._on_save_history_toggle()
        window.update()
        assert history.enabled is False
    finally:
        window.destroy()


def test_keyboard_shortcuts_mapped(tmp_path):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    settings = Settings(str(tmp_path / "settings.json"))
    history = History(str(tmp_path / "history.json"))
    window = MainWindow(settings, history)
    try:
        bindings = window.bind()
        assert "<Control-Key-comma>" in bindings
        assert "<Key-F1>" in bindings
        assert "<Control-Key-l>" in bindings
    finally:
        window.destroy()
