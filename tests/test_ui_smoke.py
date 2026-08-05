"""Interface smoke tests: import every UI module, build the main window once,
and check button/keyboard callbacks don't raise across every view.

Tkinter only reliably supports one Tk() root per process, so all GUI tests
here share a single MainWindow instance (module-scoped fixture) instead of
each creating and destroying its own - repeatedly creating Tk() roots in one
process is a known source of Tcl-level flakiness. The fixture itself skips
the whole module if no display is available (e.g. a headless CI runner
without Xvfb), so it never hangs CI.
"""

import pytest

tk = pytest.importorskip("tkinter")


def test_import_all_ui_modules():
    import cinqic_calculator.ui.about_view  # noqa: F401
    import cinqic_calculator.ui.calculator_view  # noqa: F401
    import cinqic_calculator.ui.components  # noqa: F401
    import cinqic_calculator.ui.converter_view  # noqa: F401
    import cinqic_calculator.ui.financial_view  # noqa: F401
    import cinqic_calculator.ui.history_view  # noqa: F401
    import cinqic_calculator.ui.main_window  # noqa: F401
    import cinqic_calculator.ui.settings_view  # noqa: F401


@pytest.fixture(scope="module")
def app_window(tmp_path_factory):
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.main_window import MainWindow

    base = tmp_path_factory.mktemp("smoke")
    settings = Settings(str(base / "settings.json"))
    history = History(str(base / "history.json"))
    try:
        window = MainWindow(settings, history)
    except tk.TclError:
        pytest.skip("No display available for GUI smoke test")
        return
    window.update()
    yield window
    window.destroy()


def test_main_window_creates_and_switches_every_view(app_window):
    for name in app_window.views:
        app_window.show_view(name)
        app_window.update()
    assert app_window.winfo_exists()


def test_calculator_view_button_and_keyboard_callbacks(app_window):
    app_window.show_view("Calculator")
    calc_view = app_window.views["Calculator"]
    calc_view.calc.clear_all()
    calc_view._on_button("5")
    calc_view._on_button("+")
    calc_view._on_button("3")
    calc_view._on_button("=")
    app_window.update()
    assert calc_view.calc.display == "8"

    calc_view.copy_result()
    calc_view._backspace()
    calc_view.toggle_scientific()
    calc_view._apply_scientific("square")
    app_window.update()


def test_history_view_reuse_and_delete(app_window):
    history = app_window.history
    history.clear()
    history.add("2 + 2", "4", "2026-01-01T00:00:00")

    app_window.show_view("History")
    history_view = app_window.views["History"]
    history_view.refresh()
    app_window.update()
    history_view.tree.selection_set("0")
    history_view._copy_selected()
    history_view._reuse_selected()
    app_window.update()
    assert app_window.views["Calculator"].calc.display == "4"


def test_settings_view_toggles(app_window):
    app_window.show_view("Settings")
    settings_view = app_window.views["Settings"]
    settings_view.save_history_var.set(False)
    settings_view._on_save_history_toggle()
    app_window.update()
    assert app_window.history.enabled is False
    settings_view.save_history_var.set(True)
    settings_view._on_save_history_toggle()


def test_keyboard_shortcuts_mapped(app_window):
    bindings = app_window.bind()
    assert "<Control-Key-comma>" in bindings
    assert "<Key-F1>" in bindings
    assert "<Control-Key-l>" in bindings
