"""Standard + scientific calculator screen.

Owns its own private ``Calculator()`` instance - it is never shared with, or
reachable from, any other screen. That, plus binding physical-keyboard
handling only between this screen's ``on_enter``/``on_leave``, is what keeps
this screen's state from leaking into (or being leaked into by) any other
screen - see android/logic.py's ``ScreenInputRouter`` docstring for the
desktop bug this specifically guards against.

Animation here is strictly cosmetic. Every press updates calculator state
immediately and synchronously; the visuals then catch up. Nothing waits on an
animation to finish, so hammering the keypad can never desynchronise the
displayed value from the real one.
"""

from __future__ import annotations

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen

import haptics
from widgets import SYMBOL_FONT, symbol_or_text

from cinqic_calculator.calculator import Calculator
from cinqic_calculator.expression import BINARY_OPERATORS, PreviewState
from logic import (
    animations_enabled,
    entry_animation,
    haptics_enabled,
    memory_controls_enabled,
    parenthesis_label,
    persist_memory_value,
    preview_line,
    record_history_entry,
    restore_persisted_memory,
)

_OPERATOR_KEYS = {"÷": "/", "×": "*", "−": "-", "+": "+"}

# Physical-keyboard codepoints -> the same button "value" the on-screen
# buttons send to on_button(), so both paths share one code path.
_CODEPOINT_MAP = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    ".": ".", "+": "+", "-": "−", "*": "×", "/": "÷",
    "(": "paren", ")": "paren", "%": "%", "^": "^",
}

_KEY_BACKSPACE = 8
_KEY_ENTER = 13
_KEY_NUMPAD_ENTER = 271
_KEY_ESCAPE = 27

# Display font shrinks as the value grows so long results stay on screen.
_FONT_STEPS = [(9, 46), (12, 38), (16, 30), (22, 24), (999, 18)]

# Tall enough for four six-key groups plus the handle and Done button. If the
# sheet is shorter than its contents, the inner BoxLayout overflows upward and
# the first group draws outside the sheet's own background.
_SHEET_HEIGHT_DP = 350


class CalculatorScreen(Screen):
    display_text = StringProperty("0")
    expression_text = StringProperty("")
    preview_text = StringProperty("")
    preview_color = ListProperty([0.36, 0.83, 0.36, 1])
    memory_indicator_text = StringProperty("")
    memory_controls_enabled_prop = BooleanProperty(False)
    scientific_visible = BooleanProperty(False)
    degree_mode = BooleanProperty(True)
    reduced_motion = BooleanProperty(False)
    background_color = ListProperty([0, 0, 0, 1])
    clear_label = StringProperty("AC")
    parenthesis_label = StringProperty("(")
    active_operator = StringProperty("")
    display_font_size = NumericProperty(46)
    entry_offset = NumericProperty(0)
    entry_opacity = NumericProperty(1)
    symbol_font = StringProperty(SYMBOL_FONT or "Roboto")
    backspace_label = StringProperty(symbol_or_text("\u232b", "DEL"))
    sheet_height = NumericProperty(dp(_SHEET_HEIGHT_DP))
    sheet_y = NumericProperty(-dp(_SHEET_HEIGHT_DP))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calc = Calculator()
        self._haptics_on = False

    # -- Screen lifecycle -------------------------------------------------
    def on_pre_enter(self, *_args):
        app = App.get_running_app()
        colors = app.colors
        self.background_color = _hex_to_rgba(colors["background"])
        self.calc.set_degree_mode(app.settings.get("degree_mode", True))
        self.degree_mode = self.calc.degree_mode
        self.reduced_motion = not animations_enabled(app.settings)
        self._haptics_on = haptics_enabled(app.settings)
        restore_persisted_memory(self.calc, app.settings)
        self._refresh(animate=False)
        self._sync_sheet(animate=False)

    def on_enter(self, *_args):
        Window.bind(on_key_down=self._on_key_down)

    def on_leave(self, *_args):
        Window.unbind(on_key_down=self._on_key_down)

    # -- Physical keyboard --------------------------------------------------
    def _on_key_down(self, _window, key, _scancode, codepoint, _modifiers):
        # Only bound while this screen is entered (see on_enter/on_leave), so
        # it can never fire against a screen that isn't showing.
        if key == _KEY_BACKSPACE:
            self.on_button("⌫")
            return True
        if key in (_KEY_ENTER, _KEY_NUMPAD_ENTER):
            self.on_button("=")
            return True
        if key == _KEY_ESCAPE:
            self.on_button("clear")
            return True
        value = _CODEPOINT_MAP.get(codepoint or "")
        if value is not None:
            self.on_button(value)
            return True
        return False

    # -- Button handling ------------------------------------------------
    def on_button(self, value: str):
        app = App.get_running_app()
        calc = self.calc
        self._feedback()

        if value == "clear":
            calc.clear_smart()
        elif value == "⌫":
            calc.backspace()
        elif value == "paren":
            if parenthesis_label(calc.model.open_parens, _ends_operand(calc)) == ")":
                calc.close_paren()
            else:
                calc.open_paren()
        elif value == "%":
            calc.percent()
        elif value == "±":
            calc.toggle_sign()
        elif value == ".":
            calc.input_decimal()
        elif value == "^":
            calc.push_operator("**")
        elif value in _OPERATOR_KEYS:
            calc.push_operator(_OPERATOR_KEYS[value])
        elif value == "=":
            self._commit(app)
        elif value.isdigit():
            calc.input_digit(value)

        self._refresh(animate=True, strong=value == "=")

    def _commit(self, app):
        """Press "=", recording the calculation to history exactly once."""
        before = (self.calc.last_expression, self.calc.display)
        self.calc.equals()
        if self.calc.has_error:
            return
        if (self.calc.last_expression, self.calc.display) == before:
            return
        expression = self.calc.last_expression.rstrip().removesuffix("=").rstrip()
        if expression:
            record_history_entry(app.history, expression, self.calc.plain_display)

    def on_scientific_action(self, action: str):
        """Run one scientific-sheet action described by its short code."""
        app = App.get_running_app()
        calc = self.calc
        self._feedback()
        if action.startswith("fn:"):
            calc.push_function(action[3:])
        elif action.startswith("px:"):
            calc.apply_postfix(action[3:])
        elif action.startswith("op:"):
            calc.push_operator(action[3:])
        elif action.startswith("const:"):
            calc.push_constant(action[6:])
        elif action == "ans":
            calc.push_ans()
        elif action == "pow10":
            calc.input_digit("1")
            calc.input_digit("0")
            calc.push_operator("**")
        elif action.startswith("mem:"):
            self._memory_action(action[4:], app)
        self._refresh(animate=True)

    def _memory_action(self, name, app):
        calc = self.calc
        if name == "MC" and memory_controls_enabled(calc):
            calc.memory_clear()
        elif name == "MR" and memory_controls_enabled(calc):
            calc.memory_recall()
        elif name == "M+":
            calc.memory_add()
        elif name == "M-":
            calc.memory_subtract()
        elif name == "MS":
            calc.memory_store()
        if name != "MR":
            persist_memory_value(calc, app.settings)

    def _feedback(self):
        if self._haptics_on:
            haptics.tap()

    # -- Scientific sheet ---------------------------------------------------
    def toggle_scientific(self):
        self.scientific_visible = not self.scientific_visible
        self._sync_sheet()

    def open_scientific(self):
        if not self.scientific_visible:
            self.scientific_visible = True
            self._sync_sheet()

    def close_scientific(self):
        if self.scientific_visible:
            self.scientific_visible = False
            self._sync_sheet()

    def _sheet_positions(self):
        """(shown_y, hidden_y) for the sheet.

        Uses ``sheet_height`` rather than the widget's live ``height``: during
        ``on_pre_enter`` the widget has not been laid out yet and still
        reports its default height, which left the sheet parked part-way on
        screen.
        """
        return 0, -self.sheet_height

    def _sync_sheet(self, animate: bool = True):
        sheet = self.ids.get("scientific_sheet")
        if sheet is not None:
            sheet.screen = self
            sheet.refresh_state()
        shown, hidden = self._sheet_positions()
        target = shown if self.scientific_visible else hidden
        Animation.cancel_all(self, "sheet_y")
        if animate and not self.reduced_motion:
            Animation(sheet_y=target, duration=0.22, t="out_cubic").start(self)
        else:
            self.sheet_y = target

    def drag_sheet(self, dy: float):
        shown, hidden = self._sheet_positions()
        self.sheet_y = max(hidden, min(shown, self.sheet_y + dy))

    def settle_sheet(self):
        """Snap the sheet open or closed after a drag, whichever is nearer."""
        shown, hidden = self._sheet_positions()
        midpoint = (shown + hidden) / 2.0
        self.scientific_visible = self.sheet_y > midpoint
        self._sync_sheet()

    def toggle_degree_mode(self):
        app = App.get_running_app()
        self.degree_mode = not self.degree_mode
        self.calc.set_degree_mode(self.degree_mode)
        app.settings.set("degree_mode", self.degree_mode)
        app.settings.save()
        self._refresh(animate=False)

    def apply_motion_preference(self, reduced: bool):
        """Called when the reduced-motion setting changes."""
        self.reduced_motion = bool(reduced)
        sheet = self.ids.get("scientific_sheet")
        if sheet is not None:
            sheet.refresh_state()
        if self.reduced_motion:
            Animation.cancel_all(self, "entry_offset", "entry_opacity", "sheet_y")
            self.entry_offset = 0
            self.entry_opacity = 1
            self._sync_sheet(animate=False)

    # -- Rendering --------------------------------------------------------
    def _refresh(self, animate: bool = True, strong: bool = False):
        calc = self.calc
        previous = self.display_text
        self.display_text = calc.display
        self.display_font_size = _font_size(calc.display)
        self.expression_text = calc.error_message or calc.expression_text

        preview = calc.preview()
        self.preview_text = preview_line(preview)
        self.preview_color = [0.95, 0.42, 0.42, 1] if preview.state == PreviewState.ERROR else [0.36, 0.83, 0.36, 1]

        self.memory_indicator_text = "M" if calc.has_memory else ""
        self.memory_controls_enabled_prop = memory_controls_enabled(calc)
        self.clear_label = calc.clear_label
        self.parenthesis_label = parenthesis_label(calc.model.open_parens, _ends_operand(calc))
        self.active_operator = _active_operator(calc)

        sheet = self.ids.get("scientific_sheet")
        if sheet is not None:
            sheet.refresh_state()

        if animate and self.display_text != previous:
            self._animate_entry(strong)

    def _animate_entry(self, strong: bool):
        """Give changed display text a brief rise and fade.

        Any in-flight animation is cancelled first, so fast typing retargets
        to the newest value instead of queueing up half a second of stale
        motion. The text itself is already correct before this runs.
        """
        settings = entry_animation(self.reduced_motion)
        if settings is None:
            self.entry_offset = 0
            self.entry_opacity = 1
            return
        offset_dp, duration = settings
        Animation.cancel_all(self, "entry_offset", "entry_opacity")
        if strong:
            offset_dp *= 1.6
            duration *= 1.3
        self.entry_offset = dp(offset_dp)
        self.entry_opacity = 0.35
        Animation(entry_offset=0, entry_opacity=1, duration=duration, t="out_cubic").start(self)

    def _schedule_relayout(self):
        Clock.schedule_once(self._force_relayout, 0)

    def _force_relayout(self, _dt):
        content_layout = self.ids.get("content_layout")
        if content_layout is not None:
            content_layout.do_layout()


# ----------------------------------------------------------------------
def _ends_operand(calc) -> bool:
    model = calc.model
    if model.entry is not None:
        return True
    return bool(model.tokens) and model.tokens[-1] in (")", "pi", "e", "ans", "!") or _last_is_number(model)


def _last_is_number(model) -> bool:
    if not model.tokens:
        return False
    try:
        float(model.tokens[-1])
    except ValueError:
        return False
    return True


def _active_operator(calc) -> str:
    if calc.has_error or calc.model.entry is not None:
        return ""
    tokens = calc.model.tokens
    if tokens and tokens[-1] in BINARY_OPERATORS:
        return tokens[-1]
    return ""


def _font_size(text: str) -> int:
    for threshold, size in _FONT_STEPS:
        if len(text) <= threshold:
            return size
    return _FONT_STEPS[-1][1]


def _hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return [r, g, b, 1]
