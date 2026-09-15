"""Reusable Kivy widgets for the Cinqic Calculator Android frontend.

The keypad's tactile response lives in one widget, :class:`CalcButton`, rather
than being duplicated across the three dozen buttons in calculator.kv.

The press animation scales a canvas transform, never the widget's ``size``.
Animating ``size`` would re-run the parent GridLayout's layout on every frame,
so a pressed key would nudge all of its neighbours; a canvas ``Scale`` is
purely visual and leaves the grid geometry untouched.
"""

from __future__ import annotations

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, PopMatrix, PushMatrix, RoundedRectangle, Scale
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

__all__ = ["CalcButton", "ScientificSheet", "KIND_COLORS", "SCIENTIFIC_GROUPS", "SYMBOL_FONT", "symbol_or_text"]


def _register_symbol_font():
    """Register a font that covers the symbols Roboto is missing.

    Kivy's default Roboto has no U+232B (backspace). DejaVuSans ships with
    Kivy itself, so using it costs no extra asset in the APK. If it cannot be
    found on some future Kivy layout, this returns None and callers fall back
    to a plain-text label rather than rendering an empty box.
    """
    try:
        from kivy.core.text import LabelBase
        from kivy.resources import resource_find

        path = resource_find("data/fonts/DejaVuSans.ttf")
        if not path:
            return None
        LabelBase.register(name="CinqicSymbols", fn_regular=path)
        return "CinqicSymbols"
    except Exception:
        return None


#: Name of the registered symbol font, or None when unavailable.
SYMBOL_FONT = _register_symbol_font()


def symbol_or_text(symbol: str, fallback: str) -> str:
    """Use a glyph when a font can render it, otherwise a readable word."""
    return symbol if SYMBOL_FONT else fallback

#: The scientific sheet's contents, grouped so related operations sit
#: together instead of being dumped into one undifferentiated grid. Each
#: entry is (label, action code) -- the same action vocabulary the desktop
#: view uses, so both frontends stay in step.
SCIENTIFIC_GROUPS = [
    ("Trigonometry", [("sin", "fn:sin"), ("cos", "fn:cos"), ("tan", "fn:tan"),
                      ("sin[sup]-1[/sup]", "fn:asin"), ("cos[sup]-1[/sup]", "fn:acos"), ("tan[sup]-1[/sup]", "fn:atan")]),
    ("Powers & roots", [("x[sup]2[/sup]", "px:square"), ("x[sup]3[/sup]", "px:cube"), ("x[sup]y[/sup]", "op:**"),
                        ("\u221ax", "fn:sqrt"), ("[sup]3[/sup]\u221ax", "fn:cbrt"), ("x!", "px:factorial")]),
    ("Logs & constants", [("ln", "fn:ln"), ("log", "fn:log"), ("e[sup]x[/sup]", "fn:exp"),
                          ("10[sup]x[/sup]", "pow10"), ("\u03c0", "const:pi"), ("e", "const:e")]),
    ("Memory & recall", [("MC", "mem:MC"), ("MR", "mem:MR"), ("M+", "mem:M+"),
                         ("M-", "mem:M-"), ("MS", "mem:MS"), ("Ans", "ans")]),
]


# Background / text colours per key kind, as RGBA. Kept here next to the
# widget that uses them so a theme change is one edit.
KIND_COLORS = {
    "number": ((0.13, 0.13, 0.13, 1), (1, 1, 1, 1)),
    "function": ((0.09, 0.09, 0.09, 1), (0.78, 0.78, 0.78, 1)),
    "operator": ((0.11, 0.17, 0.11, 1), (0.36, 0.83, 0.36, 1)),
    "equals": ((0.20, 0.80, 0.20, 1), (0.02, 0.02, 0.02, 1)),
    "accent": ((0.11, 0.17, 0.11, 1), (0.36, 0.83, 0.36, 1)),
}

_PRESSED_LIFT = 0.10
_DISABLED_ALPHA = 0.35


class CalcButton(ButtonBehavior, Label):
    """A calculator key with a spring press response and clear states."""

    kind = StringProperty("number")
    active = BooleanProperty(False)
    reduced_motion = BooleanProperty(False)
    corner_radius = NumericProperty(14)
    background_rgba = ListProperty([0.13, 0.13, 0.13, 1])
    #: Canvas-only scale factor. Never bound to size/size_hint.
    press_scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = kwargs.get("font_size", sp(22))
        self.markup = True
        self.halign = "center"
        self.valign = "middle"
        self._build_canvas()
        self.bind(
            pos=self._sync_graphics,
            size=self._sync_graphics,
            kind=self._sync_colors,
            active=self._sync_colors,
            disabled=self._sync_colors,
            press_scale=self._sync_graphics,
        )
        self._sync_colors()

    # ------------------------------------------------------------------
    def _build_canvas(self):
        with self.canvas.before:
            PushMatrix()
            self._scale = Scale(1, 1, 1)
            self._color = Color(*self.background_rgba)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.corner_radius)])
        with self.canvas.after:
            PopMatrix()

    def _sync_graphics(self, *_args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [dp(self.corner_radius)]
        # Scale about the button's own centre so it grows/shrinks in place.
        self._scale.origin = (self.center_x, self.center_y)
        self._scale.x = self._scale.y = self.press_scale
        self.text_size = self.size

    def _sync_colors(self, *_args):
        background, foreground = KIND_COLORS.get(self.kind, KIND_COLORS["number"])
        if self.active:
            background, foreground = KIND_COLORS["equals"]
        background = list(background)
        foreground = list(foreground)
        if self.disabled:
            background[3] = _DISABLED_ALPHA
            foreground = [foreground[0], foreground[1], foreground[2], _DISABLED_ALPHA]
        self.background_rgba = background
        self.color = foreground
        self._color.rgba = background
        self._sync_graphics()

    # ------------------------------------------------------------------
    # Press feedback
    # ------------------------------------------------------------------
    def on_press(self):
        if self.disabled:
            return
        if self.reduced_motion:
            # Motion is off: acknowledge instantly with a brightness change
            # so the key still visibly responds to the touch.
            self._color.rgba = _lift(self.background_rgba, _PRESSED_LIFT)
            return
        self._animate_to(0.96, 0.045)

    def on_release(self):
        if self.disabled:
            return
        if self.reduced_motion:
            self._color.rgba = self.background_rgba
            return
        # Rebound slightly past rest, then settle. Any in-flight animation is
        # cancelled first so hammering the keypad retargets rather than
        # queueing up a backlog of stale animations.
        Animation.cancel_all(self, "press_scale")
        (
            Animation(press_scale=1.03, duration=0.06, t="out_quad")
            + Animation(press_scale=1.0, duration=0.05, t="out_quad")
        ).start(self)

    def _animate_to(self, value, duration):
        Animation.cancel_all(self, "press_scale")
        Animation(press_scale=value, duration=duration, t="out_quad").start(self)

    def reset_motion(self):
        """Snap back to rest, e.g. when reduced motion is switched on."""
        Animation.cancel_all(self, "press_scale")
        self.press_scale = 1.0
        self._color.rgba = self.background_rgba


def _lift(rgba, amount):
    return [min(1.0, channel + amount) for channel in rgba[:3]] + [rgba[3]]


class ScientificSheet(BoxLayout):
    """The scientific drawer that slides up over the keypad.

    Sliding a sheet over the keypad, rather than expanding a panel that
    pushes everything else down, keeps the main calculator recognisable and
    avoids turning the screen into one endless vertical grid of tiny keys.

    Dragging the handle is a convenience. ``open``/``close`` are driven by
    the "fx" key and the Done button, so every scientific function stays
    reachable by tap alone -- a hidden gesture is never the only way in.
    """

    screen = ObjectProperty(None, allownone=True)
    dragging = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._memory_buttons = {}
        Clock.schedule_once(self._populate, 0)

    def _populate(self, _dt):
        """Build the grouped keys from SCIENTIFIC_GROUPS."""
        container = self.ids.get("groups")
        if container is None or container.children:
            return
        for title, entries in SCIENTIFIC_GROUPS:
            block = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60), spacing=dp(2))
            heading = Label(
                text=title, font_size=sp(11), size_hint_y=None, height=dp(15),
                halign="left", valign="middle", color=(0.55, 0.55, 0.55, 1),
            )
            heading.bind(size=lambda widget, value: setattr(widget, "text_size", value))
            block.add_widget(heading)
            row = GridLayout(cols=6, spacing=dp(6))
            for label, action in entries:
                button = CalcButton(text=label, kind="function", font_size=sp(15))
                button.bind(on_release=lambda _widget, a=action: self._fire(a))
                if action.startswith("mem:"):
                    self._memory_buttons[action[4:]] = button
                row.add_widget(button)
            block.add_widget(row)
            container.add_widget(block)
        self.refresh_state()

    def _fire(self, action):
        if self.screen is not None:
            self.screen.on_scientific_action(action)

    def refresh_state(self):
        """Mirror reduced-motion and memory-availability onto the sheet keys."""
        screen = self.screen
        if screen is None:
            return
        for button in self._iter_buttons():
            button.reduced_motion = screen.reduced_motion
        for name in ("MC", "MR"):
            button = self._memory_buttons.get(name)
            if button is not None:
                button.disabled = not screen.memory_controls_enabled_prop

    def _iter_buttons(self):
        container = self.ids.get("groups")
        if container is None:
            return
        for block in container.children:
            for child in block.children:
                for button in getattr(child, "children", []):
                    if isinstance(button, CalcButton):
                        yield button

    def on_touch_down(self, touch):
        handle = self.ids.get("drag_handle")
        if handle is not None and handle.collide_point(*touch.pos):
            self.dragging = True
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.screen is not None:
            self.screen.drag_sheet(touch.dy)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.dragging = False
            if self.screen is not None:
                self.screen.settle_sheet()
            return True
        return super().on_touch_up(touch)
