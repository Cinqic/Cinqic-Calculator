"""Pure-Python glue between the platform-independent ``cinqic_calculator``
core and the Kivy Android frontend.

Everything in this module is plain Python with no Kivy import at module
load time, on purpose: it is unit-tested directly (see
``tests/test_android_glue.py``) on a plain desktop interpreter that has no
Kivy or Android tooling installed at all. Any real *decision logic* the
Android screens need (memory-button enabled state, the persist-memory
toggle's clear-on-disable semantics, which screen currently owns hardware
key input, recording a calculation to history) belongs here, not inline in
a screen's ``.py``/``.kv`` file, precisely so it can be tested this way.
"""

from __future__ import annotations

import datetime as _datetime

from cinqic_calculator import constants
from cinqic_calculator.calculator import Calculator
from cinqic_calculator.history import History
from cinqic_calculator.settings import Settings

__all__ = [
    "resolve_data_dir",
    "memory_controls_enabled",
    "restore_persisted_memory",
    "persist_memory_value",
    "set_persist_memory",
    "record_history_entry",
    "ScreenInputRouter",
]


def resolve_data_dir(user_data_dir: str) -> str:
    """Resolve the app's private data directory from Kivy's ``user_data_dir``.

    Thin wrapper around ``constants.data_dir(override_base=...)`` so the app
    and its tests don't need to poke at the shared ``constants`` module
    directly, and so a bad/empty ``user_data_dir`` fails loudly instead of
    silently falling back to the desktop's Windows ``LOCALAPPDATA`` path.
    """
    if not user_data_dir:
        raise ValueError("user_data_dir is required to resolve the Android data directory")
    return constants.data_dir(override_base=user_data_dir)


def memory_controls_enabled(calculator: Calculator) -> bool:
    """Whether the MC/MR controls should be interactive.

    Mirrors the desktop v1.0.1 regression fix: MC/MR must be genuinely
    disabled (not just styled to look inert) whenever memory is empty, and
    must become enabled again as soon as memory holds a value.
    """
    return calculator.has_memory


def restore_persisted_memory(calculator: Calculator, settings: Settings) -> None:
    """Restore ``calculator.memory`` from settings at startup.

    Only restores when ``persist_memory`` is enabled AND the stored value is
    a genuine number. ``bool`` is deliberately excluded even though it is an
    ``int`` subclass in Python, since a stray ``True``/``False`` in
    settings.json should never be treated as a memory value.
    """
    if not settings.get("persist_memory", False):
        return
    stored = settings.get("memory_value")
    if isinstance(stored, (int, float)) and not isinstance(stored, bool):
        calculator.memory = float(stored)


def persist_memory_value(calculator: Calculator, settings: Settings) -> None:
    """Persist the current memory value to settings, if enabled.

    Call this after every memory-mutating operation (MS, MC, M+, M-) so the
    on-disk value never goes stale while persistence is turned on.
    """
    if settings.get("persist_memory", False):
        settings.set("memory_value", calculator.memory)
        settings.save()


def set_persist_memory(settings: Settings, enabled: bool) -> None:
    """Apply the "remember calculator memory between sessions" toggle.

    Regression guard for the pre-1.0.1 desktop bug where this checkbox had
    no real effect: turning persistence OFF must clear the stored memory
    value immediately (not just stop future writes), so a later re-enable
    never resurrects a stale value.
    """
    settings.set("persist_memory", bool(enabled))
    if not enabled:
        settings.set("memory_value", None)
    settings.save()


def record_history_entry(history: History, expression: str, result: str, timestamp: str | None = None) -> None:
    """Add a finished calculation to history with an ISO-8601 timestamp.

    A thin wrapper so screens don't need to import ``datetime`` or know
    ``History.add()``'s exact signature. Respects ``History.enabled``
    (driven by the ``save_history`` setting) automatically, since that
    check already lives inside ``History.add()``.
    """
    if timestamp is None:
        timestamp = _datetime.datetime.now().isoformat(timespec="seconds")
    history.add(expression, result, timestamp)


class ScreenInputRouter:
    """Tracks which screen currently "owns" hardware key / back-button input.

    Why this exists: the desktop v1.0.1 fix discovered that Tkinter
    keyboard shortcuts bound at the *toplevel* (so they work without needing
    focus) fired no matter which view was actually showing, letting
    keystrokes typed into a Financial/Convert entry field silently drive the
    hidden Calculator view's state. The fix was to guard every
    toplevel-bound handler on ``winfo_ismapped()``.

    Kivy's normal text input already avoids this class of bug: each
    screen's ``TextInput``/numeric-entry widgets are separate objects and
    only the focused one receives typed text, so there is no single shared
    "current expression" that other screens can accidentally mutate merely
    by being visible. The one place an equivalent leak *could* still creep
    in is a global ``Window``-level binding (hardware back button, a global
    keyboard-shortcut handler) that unconditionally forwards to the
    Calculator screen's ``Calculator`` instance regardless of which screen
    is actually active. Any such global binding must consult
    :meth:`is_active` before touching Calculator state - this class is that
    guard, kept as plain-Python decision logic so it's directly testable.
    """

    def __init__(self) -> None:
        self._active_screen_name: str | None = None

    def set_active(self, screen_name: str) -> None:
        self._active_screen_name = screen_name

    @property
    def active_screen_name(self) -> str | None:
        return self._active_screen_name

    def is_active(self, screen_name: str) -> bool:
        return self._active_screen_name == screen_name
