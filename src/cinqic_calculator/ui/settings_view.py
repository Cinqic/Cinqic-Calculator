"""Local settings view. Nothing here is ever transmitted anywhere."""

import tkinter as tk
from tkinter import messagebox

from .components import make_button, section_label


class SettingsView(tk.Frame):
    def __init__(self, parent, colors, settings, history, on_status=None, on_theme_change=None):
        super().__init__(parent, bg=colors["background"])
        self.colors = colors
        self.settings = settings
        self.history = history
        self.on_status = on_status or (lambda text: None)
        self.on_theme_change = on_theme_change or (lambda theme: None)
        self._build()

    def _build(self):
        c = self.colors
        section_label(self, "Settings", c, size=16).pack(anchor="w", padx=16, pady=(8, 12))

        theme_frame = tk.Frame(self, bg=c["background"])
        theme_frame.pack(fill="x", padx=16, pady=(0, 12))
        section_label(theme_frame, "Theme", c).pack(anchor="w")
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        for value, label in (("dark", "Dark"), ("light", "Light"), ("system", "System")):
            tk.Radiobutton(
                theme_frame,
                text=label,
                value=value,
                variable=self.theme_var,
                command=self._on_theme_change,
                bg=c["background"],
                fg=c["text_primary"],
                selectcolor=c["panel_alt"],
                activebackground=c["background"],
                highlightthickness=0,
            ).pack(anchor="w")

        self.save_history_var = tk.BooleanVar(value=self.settings.get("save_history", True))
        tk.Checkbutton(
            self,
            text="Save calculation history",
            variable=self.save_history_var,
            command=self._on_save_history_toggle,
            bg=c["background"],
            fg=c["text_primary"],
            selectcolor=c["panel_alt"],
            activebackground=c["background"],
            highlightthickness=0,
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self.persist_memory_var = tk.BooleanVar(value=self.settings.get("persist_memory", False))
        tk.Checkbutton(
            self,
            text="Remember calculator memory (M) between sessions",
            variable=self.persist_memory_var,
            command=self._save,
            bg=c["background"],
            fg=c["text_primary"],
            selectcolor=c["panel_alt"],
            activebackground=c["background"],
            highlightthickness=0,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        make_button(self, "Clear all history now", self._clear_history, c, kind="function", width=18, height=1, font_size=10).pack(
            anchor="w", padx=16, pady=(0, 16)
        )

        tk.Label(
            self,
            text="Settings and history stay on this device. Nothing is ever sent anywhere.",
            font=("Segoe UI", 9),
            bg=c["background"],
            fg=c["text_secondary"],
            wraplength=380,
            justify="left",
        ).pack(anchor="w", padx=16)

    def _on_theme_change(self):
        self.settings.set("theme", self.theme_var.get())
        self._save()
        self.on_theme_change(self.theme_var.get())

    def _on_save_history_toggle(self):
        enabled = self.save_history_var.get()
        self.settings.set("save_history", enabled)
        self.history.set_enabled(enabled)
        self._save()
        self.on_status("History saving " + ("enabled" if enabled else "disabled"))

    def _save(self):
        self.settings.set("persist_memory", self.persist_memory_var.get())
        self.settings.save()
        self.on_status("Settings saved")

    def _clear_history(self):
        if messagebox.askyesno("Clear history", "Delete all calculation history? This cannot be undone."):
            self.history.clear()
            self.on_status("History cleared")
