"""Tests for the Android frontend's pure-Python glue logic (android/logic.py).

These deliberately do NOT import kivy, buildozer, or anything under
android/screens/ - a running Kivy app and a GUI toolkit are not available on
this headless Windows dev machine. Only android/logic.py is plain Python
with no Kivy import at module load time, so it's the one thing here that can
be exercised directly and fast, exactly like the rest of the suite.
"""

import os

import pytest

from android.logic import (
    ScreenInputRouter,
    memory_controls_enabled,
    persist_memory_value,
    record_history_entry,
    resolve_data_dir,
    restore_persisted_memory,
    set_persist_memory,
)
from cinqic_calculator.calculator import Calculator
from cinqic_calculator.history import History
from cinqic_calculator.settings import Settings

# ---------------------------------------------------------------------------
# resolve_data_dir
# ---------------------------------------------------------------------------


def test_resolve_data_dir_uses_supplied_override_base(tmp_path):
    override_base = str(tmp_path / "kivy_user_data_dir")
    result = resolve_data_dir(override_base)
    assert result == override_base
    assert os.path.isdir(result)


def test_resolve_data_dir_rejects_empty_value():
    with pytest.raises(ValueError):
        resolve_data_dir("")

    with pytest.raises(ValueError):
        resolve_data_dir(None)


# ---------------------------------------------------------------------------
# memory_controls_enabled - MC/MR disabled-state regression coverage
# ---------------------------------------------------------------------------


def test_memory_controls_disabled_when_memory_empty():
    calc = Calculator()
    assert calc.has_memory is False
    assert memory_controls_enabled(calc) is False


def test_memory_controls_enabled_after_store():
    calc = Calculator()
    calc.display = "5"
    calc.memory_store()
    assert memory_controls_enabled(calc) is True


def test_memory_controls_disabled_again_after_clear():
    calc = Calculator()
    calc.display = "5"
    calc.memory_store()
    assert memory_controls_enabled(calc) is True

    calc.memory_clear()
    assert memory_controls_enabled(calc) is False


def test_memory_controls_enabled_after_memory_add_from_empty():
    calc = Calculator()
    calc.display = "3"
    calc.memory_add()
    assert memory_controls_enabled(calc) is True


# ---------------------------------------------------------------------------
# persist_memory_value / restore_persisted_memory / set_persist_memory
# ---------------------------------------------------------------------------


def test_persist_memory_value_writes_when_enabled(tmp_path):
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", True)
    calc = Calculator()
    calc.display = "42"
    calc.memory_store()

    persist_memory_value(calc, settings)

    reloaded = Settings(str(tmp_path / "settings.json"))
    assert reloaded.get("memory_value") == 42.0


def test_persist_memory_value_does_nothing_when_disabled(tmp_path):
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", False)
    calc = Calculator()
    calc.display = "42"
    calc.memory_store()

    persist_memory_value(calc, settings)

    reloaded = Settings(str(tmp_path / "settings.json"))
    assert reloaded.get("memory_value") is None


def test_restore_persisted_memory_applies_stored_number_when_enabled(tmp_path):
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", True)
    settings.set("memory_value", 17.5)

    calc = Calculator()
    restore_persisted_memory(calc, settings)

    assert calc.memory == 17.5
    assert calc.has_memory is True


def test_restore_persisted_memory_skips_when_disabled(tmp_path):
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", False)
    settings.set("memory_value", 17.5)

    calc = Calculator()
    restore_persisted_memory(calc, settings)

    assert calc.memory is None


def test_restore_persisted_memory_ignores_bool_stored_value(tmp_path):
    """A stray True/False must never be treated as a memory value, even
    though bool is technically an int subclass in Python."""
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", True)
    settings.set("memory_value", True)

    calc = Calculator()
    restore_persisted_memory(calc, settings)

    assert calc.memory is None


def test_set_persist_memory_enable_keeps_saving_future_updates(tmp_path):
    settings = Settings(str(tmp_path / "settings.json"))
    set_persist_memory(settings, True)

    reloaded = Settings(str(tmp_path / "settings.json"))
    assert reloaded.get("persist_memory") is True


def test_set_persist_memory_disable_clears_stored_value_immediately(tmp_path):
    """Regression: the pre-1.0.1 desktop bug where turning this off had no
    effect at all and a stale memory_value could resurface later."""
    settings = Settings(str(tmp_path / "settings.json"))
    settings.set("persist_memory", True)
    settings.set("memory_value", 99.0)
    settings.save()

    set_persist_memory(settings, False)

    assert settings.get("persist_memory") is False
    assert settings.get("memory_value") is None

    reloaded = Settings(str(tmp_path / "settings.json"))
    assert reloaded.get("persist_memory") is False
    assert reloaded.get("memory_value") is None


def test_persist_memory_toggle_round_trip_through_disk(tmp_path):
    path = str(tmp_path / "settings.json")
    settings = Settings(path)

    set_persist_memory(settings, True)
    calc = Calculator()
    calc.display = "8"
    calc.memory_store()
    persist_memory_value(calc, settings)

    restarted_settings = Settings(path)
    restarted_calc = Calculator()
    restore_persisted_memory(restarted_calc, restarted_settings)
    assert restarted_calc.memory == 8.0

    set_persist_memory(restarted_settings, False)
    reloaded_again = Settings(path)
    fresh_calc = Calculator()
    restore_persisted_memory(fresh_calc, reloaded_again)
    assert fresh_calc.memory is None


# ---------------------------------------------------------------------------
# record_history_entry / History integration
# ---------------------------------------------------------------------------


def test_record_history_entry_adds_and_persists(tmp_path):
    path = str(tmp_path / "history.json")
    history = History(path)

    record_history_entry(history, "2 + 2", "4")

    assert len(history.entries) == 1
    entry = history.entries[0]
    assert entry["expression"] == "2 + 2"
    assert entry["result"] == "4"
    assert entry["timestamp"]

    reloaded = History(path)
    assert len(reloaded.entries) == 1
    assert reloaded.entries[0]["expression"] == "2 + 2"


def test_record_history_entry_uses_supplied_timestamp(tmp_path):
    history = History(str(tmp_path / "history.json"))
    record_history_entry(history, "1 + 1", "2", timestamp="2026-08-06T00:00:00")
    assert history.entries[0]["timestamp"] == "2026-08-06T00:00:00"


def test_record_history_entry_respects_disabled_history(tmp_path):
    history = History(str(tmp_path / "history.json"), enabled=False)
    record_history_entry(history, "3 * 3", "9")
    assert history.entries == []


def test_history_delete_and_clear_via_android_logic_path(tmp_path):
    history = History(str(tmp_path / "history.json"))
    record_history_entry(history, "1 + 1", "2")
    record_history_entry(history, "2 + 2", "4")
    record_history_entry(history, "3 + 3", "6")
    assert len(history.entries) == 3

    history.delete_at(1)
    assert [e["expression"] for e in history.entries] == ["1 + 1", "3 + 3"]

    history.clear()
    assert history.entries == []

    reloaded = History(str(tmp_path / "history.json"))
    assert reloaded.entries == []


# ---------------------------------------------------------------------------
# ScreenInputRouter - cross-view input isolation guarantee
# ---------------------------------------------------------------------------


def test_screen_input_router_defaults_to_no_active_screen():
    router = ScreenInputRouter()
    assert router.active_screen_name is None
    assert router.is_active("calculator") is False


def test_screen_input_router_tracks_active_screen():
    router = ScreenInputRouter()
    router.set_active("calculator")
    assert router.active_screen_name == "calculator"
    assert router.is_active("calculator") is True
    assert router.is_active("financial") is False


def test_screen_input_router_switches_active_screen():
    router = ScreenInputRouter()
    router.set_active("calculator")
    router.set_active("financial")

    assert router.is_active("calculator") is False
    assert router.is_active("financial") is True


def test_screen_input_router_guards_against_cross_view_leak():
    """Simulates the exact scenario the desktop v1.0.1 fix addressed: a
    global key handler must only be allowed to mutate the Calculator's
    state while the Calculator screen is genuinely the active one."""
    router = ScreenInputRouter()
    calc = Calculator()

    def handle_global_digit_key(digit, active_router, target_calc):
        if not active_router.is_active("calculator"):
            return
        target_calc.input_digit(digit)

    router.set_active("financial")
    handle_global_digit_key("5", router, calc)
    handle_global_digit_key("7", router, calc)
    assert calc.display == "0"

    router.set_active("calculator")
    handle_global_digit_key("5", router, calc)
    handle_global_digit_key("7", router, calc)
    assert calc.display == "57"
