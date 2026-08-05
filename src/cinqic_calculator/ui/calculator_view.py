"""Standard + scientific calculator view."""

import datetime
import tkinter as tk

from ..calculator import Calculator
from .components import ToolTip, make_button, section_label

STANDARD_ROWS = [
    ["MC", "MR", "M+", "M-", "MS"],
    ["AC", "CE", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "-"],
    ["1", "2", "3", "+"],
    ["±", "0", ".", "="],
]

SCIENTIFIC_BUTTONS = [
    ("x²", "square"),
    ("x³", "cube"),
    ("√x", "sqrt"),
    ("∛x", "cbrt"),
    ("1/x", "reciprocal"),
    ("x!", "factorial"),
    ("|x|", "abs"),
    ("ln", "ln"),
    ("log", "log10"),
    ("sin", "sin"),
    ("cos", "cos"),
    ("tan", "tan"),
]

_MEMORY_BUTTONS = {"MC", "MR", "M+", "M-", "MS"}
_OPERATORS = {"÷": "/", "×": "*", "-": "-", "+": "+"}


class CalculatorView(tk.Frame):
    def __init__(self, parent, colors, history, on_status=None):
        super().__init__(parent, bg=colors["background"])
        self.colors = colors
        self.history = history
        self.on_status = on_status or (lambda text: None)
        self.calc = Calculator()
        self.scientific_visible = False
        self._buttons = []

        self._build()
        self.bind_all_keys()

    # ------------------------------------------------------------------
    def _build(self):
        c = self.colors

        self.expr_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 13),
            bg=c["background"],
            fg=c["text_secondary"],
            anchor="e",
        )
        self.expr_label.pack(fill="x", padx=16, pady=(16, 0))

        self.display_var = tk.StringVar(value="0")
        self.display_label = tk.Label(
            self,
            textvariable=self.display_var,
            font=("Segoe UI", 40),
            bg=c["background"],
            fg=c["text_primary"],
            anchor="e",
        )
        self.display_label.pack(fill="x", padx=16, pady=(0, 8))

        self.memory_indicator = tk.Label(
            self,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=c["background"],
            fg=c["accent"],
            anchor="e",
        )
        self.memory_indicator.pack(fill="x", padx=16)

        actions_frame = tk.Frame(self, bg=c["background"])
        actions_frame.pack(fill="x", padx=16, pady=(4, 8))
        copy_btn = make_button(actions_frame, "Copy", self.copy_result, c, kind="function", width=8, height=1, font_size=10)
        copy_btn.pack(side="left", padx=(0, 6))
        ToolTip(copy_btn, "Copy result (Ctrl+C)", c)
        sci_toggle = make_button(actions_frame, "Scientific", self.toggle_scientific, c, kind="function", width=10, height=1, font_size=10)
        sci_toggle.pack(side="left")
        self.sci_toggle_btn = sci_toggle

        self.scientific_frame = tk.Frame(self, bg=c["background"])
        self._build_scientific_row()

        self.grid_frame = tk.Frame(self, bg=c["background"])
        self.grid_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._build_standard_grid()

    def _build_scientific_row(self):
        c = self.colors
        section_label(self.scientific_frame, "Scientific", c).pack(anchor="w", pady=(0, 4))
        row_frame = tk.Frame(self.scientific_frame, bg=c["background"])
        row_frame.pack(fill="x")
        for index, (label, key) in enumerate(SCIENTIFIC_BUTTONS):
            button = make_button(
                row_frame, label, lambda k=key: self._apply_scientific(k), c,
                kind="function", width=5, height=1, font_size=11,
            )
            button.grid(row=index // 6, column=index % 6, padx=2, pady=2, sticky="nsew")
            self._buttons.append(button)

        mode_frame = tk.Frame(self.scientific_frame, bg=c["background"])
        mode_frame.pack(fill="x", pady=(4, 8))
        self.degree_var = tk.StringVar(value="DEG")
        deg_btn = make_button(mode_frame, "DEG", lambda: self._set_degree_mode(True), c, kind="function", width=6, height=1, font_size=10)
        deg_btn.pack(side="left", padx=(0, 4))
        rad_btn = make_button(mode_frame, "RAD", lambda: self._set_degree_mode(False), c, kind="function", width=6, height=1, font_size=10)
        rad_btn.pack(side="left")
        pi_btn = make_button(mode_frame, "π", lambda: self._insert_constant("pi"), c, kind="function", width=4, height=1, font_size=10)
        pi_btn.pack(side="left", padx=(12, 4))
        e_btn = make_button(mode_frame, "e", lambda: self._insert_constant("e"), c, kind="function", width=4, height=1, font_size=10)
        e_btn.pack(side="left")

    def _build_standard_grid(self):
        c = self.colors
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self._buttons = [b for b in self._buttons if not str(b) or True]

        for row_index, row in enumerate(STANDARD_ROWS):
            for col_index, value in enumerate(row):
                kind = "function"
                if value in ("÷", "×", "-", "+", "="):
                    kind = "operator"
                elif value in _MEMORY_BUTTONS:
                    kind = "function"
                elif value.isdigit() or value in (".", "±"):
                    kind = "number"

                button = make_button(
                    self.grid_frame, value, lambda v=value: self._on_button(v), c,
                    kind=kind, width=5, height=2, font_size=15,
                )
                button.grid(row=row_index, column=col_index, padx=3, pady=3, sticky="nsew")
                if value in _MEMORY_BUTTONS:
                    ToolTip(button, {"MC": "Memory clear", "MR": "Memory recall", "M+": "Memory add", "M-": "Memory subtract", "MS": "Memory store"}[value], c)

        for col in range(5):
            self.grid_frame.grid_columnconfigure(col, weight=1)

    # ------------------------------------------------------------------
    def toggle_scientific(self):
        self.scientific_visible = not self.scientific_visible
        if self.scientific_visible:
            self.scientific_frame.pack(fill="x", padx=16, before=self.grid_frame)
            self.sci_toggle_btn.config(relief="sunken")
        else:
            self.scientific_frame.pack_forget()
        self.on_status(f"Scientific mode {'on' if self.scientific_visible else 'off'}")

    def _set_degree_mode(self, degrees: bool):
        self.calc.set_degree_mode(degrees)
        self.on_status(f"Angle mode: {'degrees' if degrees else 'radians'}")

    def _apply_scientific(self, key: str):
        self.calc.apply_unary(key)
        self._refresh()
        self._record_history(f"{key}(...)")

    def _insert_constant(self, name: str):
        self.calc.insert_constant(name)
        self._refresh()

    def _on_button(self, value: str):
        if value == "AC":
            self.calc.clear_all()
        elif value == "CE":
            self.calc.clear_entry()
        elif value == "±":
            self.calc.toggle_sign()
        elif value == "%":
            self.calc.percent()
        elif value == ".":
            self.calc.input_decimal()
        elif value in _OPERATORS:
            self.calc.set_operator(_OPERATORS[value])
        elif value == "=":
            expression = self._current_expression_text()
            self.calc.equals()
            self._record_history(expression)
        elif value == "MC":
            self.calc.memory_clear()
        elif value == "MR":
            self.calc.memory_recall()
        elif value == "M+":
            self.calc.memory_add()
        elif value == "M-":
            self.calc.memory_subtract()
        elif value == "MS":
            self.calc.memory_store()
        elif value.isdigit():
            self.calc.input_digit(value)
        self._refresh()

    def _current_expression_text(self) -> str:
        if self.calc.pending_operator and self.calc.stored_value is not None:
            op_symbol = {v: k for k, v in _OPERATORS.items()}.get(self.calc.pending_operator, self.calc.pending_operator)
            return f"{self.calc._format(self.calc.stored_value)} {op_symbol} {self.calc.display}"
        return self.calc.display

    def _record_history(self, expression: str):
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        self.history.add(expression, self.calc.display, timestamp)

    def _refresh(self):
        self.display_var.set(self.calc.display)
        self.memory_indicator.config(text="M" if self.calc.has_memory else "")

    # ------------------------------------------------------------------
    def copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.calc.display)
        self.on_status("Result copied")

    def paste_expression(self):
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            return
        cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
        if not cleaned:
            return
        self.calc.clear_entry()
        for ch in cleaned:
            if ch == ".":
                self.calc.input_decimal()
            elif ch == "-":
                if self.calc.display == "0":
                    self.calc.toggle_sign()
            else:
                self.calc.input_digit(ch)
        self._refresh()
        self.on_status("Expression pasted")

    def use_result_in_history(self, result_text: str):
        self.calc.clear_all()
        for ch in result_text:
            if ch == ".":
                self.calc.input_decimal()
            elif ch == "-":
                self.calc.toggle_sign()
            elif ch.isdigit():
                self.calc.input_digit(ch)
        self._refresh()

    # ------------------------------------------------------------------
    def bind_all_keys(self):
        top = self.winfo_toplevel()
        for digit in "0123456789":
            top.bind(f"<Key-{digit}>", lambda e, d=digit: self._on_button(d))
        top.bind("<Key-period>", lambda e: self._on_button("."))
        top.bind("<Key-plus>", lambda e: self._on_button("+"))
        top.bind("<Key-minus>", lambda e: self._on_button("-"))
        top.bind("<Key-asterisk>", lambda e: self._on_button("×"))
        top.bind("<Key-slash>", lambda e: self._on_button("÷"))
        top.bind("<Return>", lambda e: self._on_button("="))
        top.bind("<KP_Enter>", lambda e: self._on_button("="))
        top.bind("<Escape>", lambda e: self._on_button("CE"))
        top.bind("<BackSpace>", lambda e: self._backspace())

    def _backspace(self):
        self.calc.backspace()
        self._refresh()
