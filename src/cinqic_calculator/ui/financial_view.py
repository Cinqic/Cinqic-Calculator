"""Percentage, price, and interest tools. Results are estimates, not advice."""

import tkinter as tk
from tkinter import ttk

from .. import financial
from .components import make_button, section_label, styled_entry


class FinancialView(tk.Frame):
    def __init__(self, parent, colors, on_status=None):
        super().__init__(parent, bg=colors["background"])
        self.colors = colors
        self.on_status = on_status or (lambda text: None)
        self._build()

    def _build(self):
        c = self.colors
        section_label(self, "Financial", c, size=16).pack(anchor="w", padx=16, pady=(8, 0))
        tk.Label(
            self,
            text="Practical estimates for everyday math. Not tax, accounting, or investment advice.",
            font=("Segoe UI", 9),
            bg=c["background"],
            fg=c["text_secondary"],
            wraplength=380,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._build_percentage_tab(notebook)
        self._build_price_tab(notebook)
        self._build_interest_tab(notebook)

    # ------------------------------------------------------------------
    def _result_row(self, parent, label_text="Result"):
        c = self.colors
        frame = tk.Frame(parent, bg=c["panel"], highlightbackground=c["border"], highlightthickness=1)
        frame.pack(fill="x", pady=(12, 0))
        section_label(frame, label_text, c).pack(anchor="w", padx=10, pady=(8, 0))
        result_var = tk.StringVar(value="")
        tk.Label(frame, textvariable=result_var, font=("Segoe UI", 16), bg=c["panel"], fg=c["text_primary"]).pack(
            anchor="w", padx=10, pady=(0, 8)
        )
        return result_var

    def _labeled_entry(self, parent, label_text):
        c = self.colors
        section_label(parent, label_text, c, size=10).pack(anchor="w", pady=(6, 2))
        var = tk.StringVar()
        entry = styled_entry(parent, c, textvariable=var, width=24)
        entry.pack(anchor="w")
        return var

    def _safe_float(self, var: tk.StringVar, default=0.0) -> float:
        try:
            return float(var.get())
        except (ValueError, TypeError):
            return default

    # -- Percentage tab ---------------------------------------------------
    def _build_percentage_tab(self, notebook):
        c = self.colors
        tab = tk.Frame(notebook, bg=c["background"])
        notebook.add(tab, text="Percentage")

        number_var = self._labeled_entry(tab, "Number")
        percent_var = self._labeled_entry(tab, "Percent")
        result_var = self._result_row(tab, "Percentage of number")

        def calculate(*_):
            try:
                value = financial.percentage_of(self._safe_float(number_var), self._safe_float(percent_var))
                result_var.set(f"{value:g}")
            except Exception:
                result_var.set("Enter valid numbers")

        make_button(tab, "Calculate", calculate, c, kind="operator", width=12, height=1).pack(anchor="w", pady=(10, 0))

        old_var = self._labeled_entry(tab, "Original value (for increase/decrease/difference)")
        pct_var = self._labeled_entry(tab, "Percent")
        result_inc = self._result_row(tab, "Increase")
        result_dec = self._result_row(tab, "Decrease")

        def calc_inc_dec(*_):
            try:
                base = self._safe_float(old_var)
                pct = self._safe_float(pct_var)
                result_inc.set(f"{financial.percentage_increase(base, pct):g}")
                result_dec.set(f"{financial.percentage_decrease(base, pct):g}")
            except Exception:
                result_inc.set("Enter valid numbers")
                result_dec.set("")

        make_button(tab, "Calculate", calc_inc_dec, c, kind="operator", width=12, height=1).pack(anchor="w", pady=(10, 0))

    # -- Price tab ----------------------------------------------------------
    def _build_price_tab(self, notebook):
        c = self.colors
        tab = tk.Frame(notebook, bg=c["background"])
        notebook.add(tab, text="Price")

        price_var = self._labeled_entry(tab, "Price")
        discount_var = self._labeled_entry(tab, "Discount %")
        tax_var = self._labeled_entry(tab, "Sales tax %")
        result_var = self._result_row(tab, "Final price")

        def calculate(*_):
            try:
                value = financial.final_price(
                    self._safe_float(price_var), self._safe_float(discount_var), self._safe_float(tax_var)
                )
                result_var.set(f"${value:,.2f}")
            except Exception:
                result_var.set("Enter valid numbers")

        make_button(tab, "Calculate", calculate, c, kind="operator", width=12, height=1).pack(anchor="w", pady=(10, 0))

        bill_var = self._labeled_entry(tab, "Bill total")
        tip_var = self._labeled_entry(tab, "Tip %")
        people_var = self._labeled_entry(tab, "Split between (people)")
        tip_result = self._result_row(tab, "Tip amount")
        split_result = self._result_row(tab, "Per person (with tip)")

        def calc_tip(*_):
            try:
                bill = self._safe_float(bill_var)
                tip_pct = self._safe_float(tip_var)
                tip_result.set(f"${financial.tip(bill, tip_pct):,.2f}")
                people = int(self._safe_float(people_var, 1)) or 1
                split_result.set(f"${financial.split_bill(bill, people, tip_pct):,.2f}")
            except Exception:
                tip_result.set("Enter valid numbers")
                split_result.set("")

        make_button(tab, "Calculate", calc_tip, c, kind="operator", width=12, height=1).pack(anchor="w", pady=(10, 0))

    # -- Interest tab ---------------------------------------------------------
    def _build_interest_tab(self, notebook):
        c = self.colors
        tab = tk.Frame(notebook, bg=c["background"])
        notebook.add(tab, text="Interest")

        principal_var = self._labeled_entry(tab, "Principal")
        rate_var = self._labeled_entry(tab, "Annual interest rate %")
        years_var = self._labeled_entry(tab, "Number of years")
        frequency_var = self._labeled_entry(tab, "Compounding periods per year (1=annual, 12=monthly)")
        simple_result = self._result_row(tab, "Simple interest earned (estimate)")
        compound_result = self._result_row(tab, "Compound total value (estimate)")

        def calculate(*_):
            try:
                principal = self._safe_float(principal_var)
                rate = self._safe_float(rate_var)
                years = self._safe_float(years_var)
                frequency = int(self._safe_float(frequency_var, 1)) or 1
                simple_result.set(f"${financial.simple_interest(principal, rate, years):,.2f}")
                compound_result.set(f"${financial.compound_interest(principal, rate, years, frequency):,.2f}")
            except Exception:
                simple_result.set("Enter valid numbers")
                compound_result.set("")

        make_button(tab, "Calculate", calculate, c, kind="operator", width=12, height=1).pack(anchor="w", pady=(10, 0))
        tk.Label(
            tab,
            text="Estimates only. Growth is never guaranteed.",
            font=("Segoe UI", 9),
            bg=c["background"],
            fg=c["text_secondary"],
        ).pack(anchor="w", pady=(8, 0))
