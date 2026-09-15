"""Optional, permission-free haptic feedback for the Android frontend.

Uses ``View.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)``,
which is the system's own touch-feedback path and requires **no** Android
permission. The ``VIBRATE`` permission is only needed by the ``Vibrator`` /
``VibrationEffect`` APIs, which this app deliberately does not touch -- the
app's manifest stays empty of permissions.

Everything here degrades silently: off-device (desktop, CI, unit tests) there
is no pyjnius and no activity, so :func:`tap` becomes a no-op and
:func:`is_available` reports ``False`` rather than pretending haptics work.
"""

from __future__ import annotations

__all__ = ["is_available", "tap", "reset"]

_state = {"checked": False, "view": None, "constant": None}


def _resolve():
    """Look up the decor view and haptic constant once, tolerating absence."""
    if _state["checked"]:
        return
    _state["checked"] = True
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        if activity is None:
            return
        constants = autoclass("android.view.HapticFeedbackConstants")
        _state["view"] = activity.getWindow().getDecorView()
        _state["constant"] = constants.VIRTUAL_KEY
    except Exception:
        # Not on Android, pyjnius missing, or the activity is not up yet.
        # Either way there is nothing to vibrate; stay quiet.
        _state["view"] = None
        _state["constant"] = None


def is_available() -> bool:
    """Whether real device haptics can actually be triggered right now."""
    _resolve()
    return _state["view"] is not None


def tap() -> bool:
    """Play one short key-press haptic. Returns whether it actually fired."""
    _resolve()
    view = _state["view"]
    if view is None:
        return False
    try:
        view.performHapticFeedback(_state["constant"])
        return True
    except Exception:
        # A device or ROM that refuses the call should disable haptics for
        # the rest of the session rather than raising on every keypress.
        _state["view"] = None
        return False


def reset() -> None:
    """Forget the cached lookup (used by tests)."""
    _state.update({"checked": False, "view": None, "constant": None})
