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


# ---------------------------------------------------------------------------
# Regression tests: v1.0.1 memory-state and keyboard-leak fixes
# ---------------------------------------------------------------------------
def _find_entries(widget):
    found = []
    for child in widget.winfo_children():
        if child.winfo_class() == "Entry":
            found.append(child)
        found.extend(_find_entries(child))
    return found


def test_memory_indicator_and_buttons_disabled_when_empty(app_window):
    app_window.show_view("Calculator")
    calc_view = app_window.views["Calculator"]
    calc_view.calc.memory_clear()
    calc_view._refresh()
    app_window.update()

    assert calc_view.memory_indicator.cget("text") == ""
    assert str(calc_view.mc_button.cget("state")) == "disabled"
    assert str(calc_view.mr_button.cget("state")) == "disabled"


def test_memory_buttons_enable_after_store_and_disable_after_clear(app_window):
    app_window.show_view("Calculator")
    calc_view = app_window.views["Calculator"]
    calc_view.calc.clear_all()
    calc_view._refresh()

    calc_view._on_button("5")
    calc_view._on_button("MS")
    app_window.update()
    assert calc_view.memory_indicator.cget("text") == "M"
    assert str(calc_view.mc_button.cget("state")) == "normal"
    assert str(calc_view.mr_button.cget("state")) == "normal"

    calc_view._on_button("MC")
    app_window.update()
    assert calc_view.memory_indicator.cget("text") == ""
    assert str(calc_view.mc_button.cget("state")) == "disabled"
    assert str(calc_view.mr_button.cget("state")) == "disabled"


def test_keyboard_input_does_not_leak_from_other_views_to_calculator(app_window):
    """Regression: typing into a Financial/Convert entry field must not
    silently drive the (invisible) Calculator view's state, since keyboard
    shortcuts are bound at the toplevel and previously fired regardless of
    which view was actually showing."""
    app_window.show_view("Calculator")
    calc_view = app_window.views["Calculator"]
    calc_view.calc.clear_all()
    calc_view._refresh()

    app_window.show_view("Financial")
    app_window.update()
    entries = _find_entries(app_window.views["Financial"])
    assert entries, "Financial view should have entry fields"
    entry = entries[0]
    entry.focus_set()
    app_window.update()

    app_window.event_generate("<Key-5>")
    app_window.event_generate("<Key-7>")
    app_window.update()

    assert entry.get() == "57"
    assert calc_view.calc.display == "0"

    app_window.show_view("Calculator")


def test_memory_restores_on_init_when_persist_memory_enabled(app_window, tmp_path):
    """Regression: the 'Remember calculator memory between sessions' setting
    previously did nothing - memory was never actually restored on startup.
    Builds a second CalculatorView under the already-open window (instead of
    a second Tk() root, which is flaky to create/destroy repeatedly in one
    process) to exercise the same settings-driven init path a real restart
    would take."""
    from cinqic_calculator.history import History
    from cinqic_calculator.settings import Settings
    from cinqic_calculator.ui.calculator_view import CalculatorView

    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", True)
    settings.set("memory_value", 42.0)
    settings.save()
    history = History(str(tmp_path / "history.json"))

    view = CalculatorView(app_window, app_window.colors, history, settings)
    app_window.update()
    try:
        assert view.calc.memory == 42.0
        assert view.memory_indicator.cget("text") == "M"
        assert str(view.mc_button.cget("state")) == "normal"
    finally:
        view.destroy()


def test_persist_memory_toggle_off_clears_stored_value(app_window):
    """Regression: settings.json didn't have a memory_value key in
    DEFAULT_SETTINGS, so Settings.load() silently dropped it on reload
    regardless of the persist_memory checkbox's state."""
    settings_view = app_window.views["Settings"]
    settings_view.settings.set("memory_value", 99.0)
    settings_view.persist_memory_var.set(False)
    settings_view._on_persist_memory_toggle()
    assert settings_view.settings.get("memory_value") is None
