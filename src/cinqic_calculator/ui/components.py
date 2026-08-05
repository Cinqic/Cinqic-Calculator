"""Small reusable themed widgets shared across views."""

import tkinter as tk
from tkinter import ttk

FONT_FAMILY = "Segoe UI"


class ToolTip:
    """A simple delayed tooltip for widgets whose label is a symbol."""

    def __init__(self, widget, text: str, colors: dict):
        self.widget = widget
        self.text = text
        self.colors = colors
        self.tip_window = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, _event=None):
        self.widget.after(500, self._show)

    def _show(self):
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
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


def make_button(parent, text, command, colors, kind="number", width=6, height=2, font_size=14):
    """Create a flat, themed tk.Button with visible keyboard focus."""
    if kind == "operator":
        bg, fg, active_bg = colors["accent"], "#000000", colors["accent_active"]
    elif kind == "function":
        bg, fg, active_bg = colors["panel_alt"], colors["text_primary"], colors["border"]
    else:
        bg, fg, active_bg = colors["panel"], colors["text_primary"], colors["panel_alt"]

    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=(FONT_FAMILY, font_size),
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
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
    return button


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
