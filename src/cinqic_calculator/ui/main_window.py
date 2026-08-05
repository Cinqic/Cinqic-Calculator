"""Main application window: sidebar navigation + view switching."""

import tkinter as tk
from tkinter import ttk

from .. import constants
from .about_view import AboutView
from .calculator_view import CalculatorView
from .components import configure_ttk_theme
from .converter_view import ConverterView
from .financial_view import FinancialView
from .history_view import HistoryView
from .settings_view import SettingsView

_NAV_ITEMS = ["Calculator", "Convert", "Financial", "History", "Settings", "About"]
_MIN_WIDTH = 640
_MIN_HEIGHT = 480


class MainWindow(tk.Tk):
    def __init__(self, settings, history):
        super().__init__()
        self.settings = settings
        self.history = history
        self.theme_name = constants.resolve_theme(settings.get("theme", "dark"))
        self.colors = constants.get_colors(self.theme_name)

        self.title(constants.APP_NAME)
        self.minsize(_MIN_WIDTH, _MIN_HEIGHT)
        self._restore_geometry()
        self.configure(bg=self.colors["background"])

        self.style = ttk.Style(self)
        configure_ttk_theme(self.style, self.colors)

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Control-comma>", lambda e: self.show_view("Settings"))
        self.bind("<F1>", lambda e: self.show_view("About"))
        self.bind("<Control-l>", lambda e: self._clear_history_shortcut())
        self.bind("<Control-c>", lambda e: self._copy_shortcut())
        self.bind("<Control-v>", lambda e: self._paste_shortcut())

    def _restore_geometry(self):
        width = self.settings.get("window_width", 900) or 900
        height = self.settings.get("window_height", 600) or 600
        x = self.settings.get("window_x")
        y = self.settings.get("window_y")
        if x is not None and y is not None:
            self.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.geometry(f"{width}x{height}")

    def _build_layout(self):
        c = self.colors
        top_bar = tk.Frame(self, bg=c["panel"], height=40)
        top_bar.pack(fill="x", side="top")
        tk.Label(
            top_bar, text="Cinqic Calculator", font=("Segoe UI", 11, "bold"), bg=c["panel"], fg=c["text_primary"]
        ).pack(side="left", padx=12, pady=8)
        tk.Label(
            top_bar, text="Local • Offline", font=("Segoe UI", 9), bg=c["panel"], fg=c["accent"]
        ).pack(side="right", padx=12, pady=8)

        body = tk.Frame(self, bg=c["background"])
        body.pack(fill="both", expand=True)

        self.nav_frame = tk.Frame(body, bg=c["panel"], width=140)
        self.nav_frame.pack(side="left", fill="y")

        self.content_frame = tk.Frame(body, bg=c["background"])
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self, textvariable=self.status_var, font=("Segoe UI", 8), bg=c["panel"], fg=c["text_secondary"], anchor="w"
        )
        status_bar.pack(fill="x", side="bottom")

        self.nav_buttons = {}
        for name in _NAV_ITEMS:
            button = tk.Button(
                self.nav_frame,
                text=name,
                command=lambda n=name: self.show_view(n),
                font=("Segoe UI", 10),
                bg=c["panel"],
                fg=c["text_primary"],
                activebackground=c["panel_alt"],
                activeforeground=c["text_primary"],
                bd=0,
                relief="flat",
                anchor="w",
                highlightthickness=1,
                highlightbackground=c["panel"],
                highlightcolor=c["accent"],
                takefocus=True,
                padx=12,
                pady=10,
            )
            button.pack(fill="x")
            self.nav_buttons[name] = button

        self.views = {
            "Calculator": CalculatorView(self.content_frame, c, self.history, on_status=self.set_status),
            "Convert": ConverterView(self.content_frame, c, on_status=self.set_status),
            "Financial": FinancialView(self.content_frame, c, on_status=self.set_status),
            "History": HistoryView(
                self.content_frame, c, self.history, on_status=self.set_status, on_reuse=self._reuse_in_calculator
            ),
            "Settings": SettingsView(
                self.content_frame, c, self.settings, self.history, on_status=self.set_status, on_theme_change=self.apply_theme
            ),
            "About": AboutView(self.content_frame, c),
        }
        self.show_view("Calculator")

    def show_view(self, name: str):
        for view in self.views.values():
            view.pack_forget()
        self.views[name].pack(fill="both", expand=True)
        if name == "History":
            self.views["History"].refresh()
        for nav_name, button in self.nav_buttons.items():
            button.config(bg=self.colors["accent"] if nav_name == name else self.colors["panel"])
        self.set_status(f"{name} view")

    def set_status(self, text: str):
        self.status_var.set(text)

    def _reuse_in_calculator(self, result_text: str):
        self.views["Calculator"].use_result_in_history(result_text)
        self.show_view("Calculator")

    def _clear_history_shortcut(self):
        self.show_view("History")

    def _copy_shortcut(self):
        current = self.focus_get()
        calculator_view = self.views["Calculator"]
        if calculator_view.winfo_ismapped():
            calculator_view.copy_result()

    def _paste_shortcut(self):
        calculator_view = self.views["Calculator"]
        if calculator_view.winfo_ismapped():
            calculator_view.paste_expression()

    def apply_theme(self, theme_name: str):
        self.theme_name = constants.resolve_theme(theme_name)
        self.set_status("Theme changes apply after restart")

    def _on_close(self):
        self.settings.set("window_width", self.winfo_width())
        self.settings.set("window_height", self.winfo_height())
        self.settings.set("window_x", self.winfo_x())
        self.settings.set("window_y", self.winfo_y())
        self.settings.save()
        self.destroy()
