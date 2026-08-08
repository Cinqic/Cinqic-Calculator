"""Standard + scientific calculator screen.

Owns its own private ``Calculator()`` instance - it is never shared with,
or reachable from, any other screen. That, plus binding physical-keyboard
handling only between this screen's ``on_enter``/``on_leave``, is what keeps
this screen's state from leaking into (or being leaked into by) any other
screen - see android/logic.py's ``ScreenInputRouter`` docstring for the
desktop bug this specifically guards against.
"""

from __future__ import annotations

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

from cinqic_calculator.calculator import Calculator
from logic import memory_controls_enabled, persist_memory_value, record_history_entry, restore_persisted_memory

_OPERATORS = {"÷", "×", "-", "+"}

_UNARY_FUNCTIONS = {
    "x²": "square",
    "x³": "cube",
    "√x": "sqrt",
    "∛x": "cbrt",
    "1/x": "reciprocal",
    "x!": "factorial",
    "|x|": "abs",
    "ln": "ln",
    "log": "log10",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
}

# Physical-keyboard codepoints -> the same button "value" the on-screen
# buttons send to on_button(), so both paths share one code path.
_CODEPOINT_MAP = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    ".": ".", "+": "+", "-": "-", "*": "×", "/": "÷",
}

# Window.on_key_down's integer `key` codes for the control keys that don't
# have a useful codepoint of their own.
_KEY_BACKSPACE = 8
_KEY_ENTER = 13
_KEY_NUMPAD_ENTER = 271
_KEY_ESCAPE = 27


class CalculatorScreen(Screen):
    display_text = StringProperty("0")
    memory_indicator_text = StringProperty("")
    memory_controls_enabled_prop = BooleanProperty(False)
    scientific_visible = BooleanProperty(False)
    degree_mode = BooleanProperty(True)
    background_color = ListProperty([0, 0, 0, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calc = Calculator()

    # -- Screen lifecycle -------------------------------------------------
    def on_pre_enter(self, *_args):
        app = App.get_running_app()
        colors = app.colors
        self.background_color = _hex_to_rgba(colors["background"])
        self.calc.set_degree_mode(app.settings.get("degree_mode", True))
        self.degree_mode = self.calc.degree_mode
        restore_persisted_memory(self.calc, app.settings)
        self._refresh()
        # Re-entering this screen (including after an app restart, where
        # scientific_visible defaults back to False) must never leave a
        # layout pass from a previous visit stale.
        self._schedule_relayout()

    def on_enter(self, *_args):
        Window.bind(on_key_down=self._on_key_down)

    def on_leave(self, *_args):
        Window.unbind(on_key_down=self._on_key_down)

    # -- Physical keyboard --------------------------------------------------
    def _on_key_down(self, _window, key, _scancode, codepoint, _modifiers):
        # Only bound while this screen is entered (see on_enter/on_leave
        # above), so it can never fire against a screen that isn't showing.
        if key == _KEY_BACKSPACE:
            self.on_button("⌫")
            return True
        if key in (_KEY_ENTER, _KEY_NUMPAD_ENTER):
            self.on_button("=")
            return True
        if key == _KEY_ESCAPE:
            self.on_button("CE")
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

        if value == "C":
            calc.clear_all()
        elif value == "CE":
            calc.clear_entry()
        elif value == "⌫":  # backspace
            calc.backspace()
        elif value == "%":
            calc.percent()
        elif value == "+/-":
            calc.toggle_sign()
        elif value == ".":
            calc.input_decimal()
        elif value in _OPERATORS:
            calc.set_operator("*" if value == "×" else "/" if value == "÷" else value)
        elif value == "=":
            expression_before = calc.display
            pending = calc.pending_operator
            stored = calc.stored_value
            calc.equals()
            if calc.display != "Error" and pending is not None and stored is not None:
                expression = f"{_format_operand(stored)} {pending} {expression_before}"
                record_history_entry(app.history, expression, calc.display)
        elif value == "MC":
            if memory_controls_enabled(calc):
                calc.memory_clear()
                persist_memory_value(calc, app.settings)
        elif value == "MR":
            if memory_controls_enabled(calc):
                calc.memory_recall()
        elif value == "M+":
            calc.memory_add()
            persist_memory_value(calc, app.settings)
        elif value == "M-":
            calc.memory_subtract()
            persist_memory_value(calc, app.settings)
        elif value == "MS":
            calc.memory_store()
            persist_memory_value(calc, app.settings)
        elif value.isdigit():
            calc.input_digit(value)

        self._refresh()

    def on_scientific_button(self, value: str):
        calc = self.calc
        if value == "pi":
            calc.insert_constant("pi")
        elif value == "e":
            calc.insert_constant("e")
        elif value in _UNARY_FUNCTIONS:
            calc.apply_unary(_UNARY_FUNCTIONS[value])
        self._refresh()

    def toggle_scientific(self):
        self.scientific_visible = not self.scientific_visible
        self._schedule_relayout()

    def _schedule_relayout(self):
        # Bug fix: collapsing the Scientific panel left the display and
        # memory row visually offset above the screen until the user
        # manually interacted with something. content_layout's children
        # size_hint_y bindings (see calculator.kv) update immediately, but
        # Kivy's own layout recompute for a BoxLayout is itself deferred to
        # the next Clock tick (via Layout._trigger_layout) -- on a real
        # device this could be observed a frame late, or not settle into a
        # consistent state across the opacity/disabled/size_hint changes
        # firing together. Explicitly forcing do_layout() one frame later,
        # after kv's own bindings have already fired, guarantees the
        # rendered result matches scientific_visible's current value rather
        # than depending on however Kivy happened to batch that frame's
        # updates. See financial_screen.py's _reset_scroll() for the
        # equivalent fix on a screen that uses an actual ScrollView.
        Clock.schedule_once(self._force_relayout, 0)

    def _force_relayout(self, _dt):
        content_layout = self.ids.get("content_layout")
        if content_layout is not None:
            content_layout.do_layout()

    def toggle_degree_mode(self):
        app = App.get_running_app()
        self.degree_mode = not self.degree_mode
        self.calc.set_degree_mode(self.degree_mode)
        app.settings.set("degree_mode", self.degree_mode)
        app.settings.save()

    # -- Rendering --------------------------------------------------------
    def _refresh(self):
        self.display_text = self.calc.display
        self.memory_indicator_text = "M" if self.calc.has_memory else ""
        self.memory_controls_enabled_prop = memory_controls_enabled(self.calc)


def _format_operand(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return str(value)


def _hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return [r, g, b, 1]
