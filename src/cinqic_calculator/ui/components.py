"""Small reusable themed widgets shared across views."""

import tkinter as tk
from tkinter import ttk

from ..constants import readable_text_on

FONT_FAMILY = "Segoe UI"


class ToolTip:
    """A simple delayed tooltip for widgets whose label is a symbol."""

    def __init__(self, widget, text: str, colors: dict):
        self.widget = widget
        self.text = text
        self.colors = colors
        self.tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(500, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        self._after_id = None
        if self.tip_window or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            background=self.colors["panel_alt"],
            foreground=self.colors["text_primary"],
            relief="solid",
            borderwidth=1,
            font=(FONT_FAMILY, 9),
            padx=6,
            pady=3,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self.tip_window is not None:
            try:
                self.tip_window.destroy()
            except tk.TclError:
                pass
            self.tip_window = None


def button_palette(colors: dict, kind: str):
    """Resolve (background, foreground, active background) for a button kind."""
    if kind == "equals":
        return colors["accent"], readable_text_on(colors["accent"]), colors["accent_active"]
    if kind == "operator":
        return colors["panel_alt"], colors["accent"], colors["border"]
    if kind == "function":
        return colors["panel_alt"], colors["text_primary"], colors["border"]
    return colors["panel"], colors["text_primary"], colors["panel_alt"]


def make_button(parent, text, command, colors, kind="number", width=6, height=2, font_size=14):
    """Create a flat, themed tk.Button with hover and visible keyboard focus.

    Desktop feedback is deliberately colour-based rather than an imitation of
    the Android keypad's spring animation: Tkinter has no compositor-backed
    transform, so "scaling" a button means resizing the widget, which reflows
    the whole grid. A crisp hover/press colour change reads as responsive
    without ever moving the layout.
    """
    background, foreground, active_background = button_palette(colors, kind)

    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=(FONT_FAMILY, font_size),
        bg=background,
        fg=foreground,
        activebackground=active_background,
        activeforeground=foreground,
        bd=0,
        relief="flat",
        highlightthickness=2,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        width=width,
        height=height,
        cursor="hand2",
        takefocus=True,
    )
    button._cinqic_kind = kind
    button._cinqic_active = False

    def on_enter(_event):
        if button["state"] != "disabled" and not button._cinqic_active:
            button.config(bg=active_background)

    def on_leave(_event):
        if not button._cinqic_active:
            button.config(bg=background)

    button.bind("<Enter>", on_enter, add="+")
    button.bind("<Leave>", on_leave, add="+")
    return button


def set_button_active(button, active: bool, colors: dict, kind: str | None = None):
    """Mark a button as the currently-selected one (e.g. the pending operator).

    The state is shown with a filled background *and* a sunken relief, so it
    is not conveyed by colour alone.
    """
    kind = kind or getattr(button, "_cinqic_kind", "function")
    background, foreground, _ = button_palette(colors, kind)
    button._cinqic_active = bool(active)
    if active:
        button.config(bg=colors["accent"], fg=readable_text_on(colors["accent"]), relief="sunken")
    else:
        button.config(bg=background, fg=foreground, relief="flat")


def section_label(parent, text, colors, size=11):
    return tk.Label(
        parent,
        text=text,
        font=(FONT_FAMILY, size, "bold"),
        bg=colors["background"],
        fg=colors["text_secondary"],
        anchor="w",
    )


def styled_entry(parent, colors, textvariable=None, width=16):
    return tk.Entry(
        parent,
        textvariable=textvariable,
        font=(FONT_FAMILY, 12),
        bg=colors["panel_alt"],
        fg=colors["text_primary"],
        insertbackground=colors["text_primary"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=colors["border"],
        highlightcolor=colors["accent"],
        width=width,
    )


def configure_ttk_theme(style: ttk.Style, colors: dict):
    style.theme_use("default")
    style.configure(
        "Cinqic.TCombobox",
        fieldbackground=colors["panel_alt"],
        background=colors["panel_alt"],
        foreground=colors["text_primary"],
        arrowcolor=colors["text_primary"],
    )
    style.configure(
        "Cinqic.Treeview",
        background=colors["panel"],
        fieldbackground=colors["panel"],
        foreground=colors["text_primary"],
        borderwidth=0,
    )
    style.configure(
        "Cinqic.Treeview.Heading",
        background=colors["panel_alt"],
        foreground=colors["text_secondary"],
    )
    style.map(
        "Cinqic.Treeview",
        background=[("selected", colors["accent"])],
        foreground=[("selected", "#000000")],
    )
