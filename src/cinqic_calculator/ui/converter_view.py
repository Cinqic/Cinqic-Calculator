"""Unit conversion view."""

import tkinter as tk
from tkinter import ttk

from ..conversions import CATEGORIES, ConversionError, convert
from .components import section_label, styled_entry

_CATEGORY_LABELS = {
    "length": "Length",
    "mass": "Weight / Mass",
    "temperature": "Temperature",
    "area": "Area",
    "volume": "Volume",
    "speed": "Speed",
    "time": "Time",
    "data_storage": "Data Storage",
}

_TEMPERATURE_UNITS = ["celsius", "fahrenheit", "kelvin"]

_UNIT_LABELS = {
    "millimeter": "Millimeters (mm)",
    "centimeter": "Centimeters (cm)",
    "meter": "Meters (m)",
    "kilometer": "Kilometers (km)",
    "inch": "Inches (in)",
    "foot": "Feet (ft)",
    "yard": "Yards (yd)",
    "mile": "Miles (mi)",
    "milligram": "Milligrams (mg)",
    "gram": "Grams (g)",
    "kilogram": "Kilograms (kg)",
    "ounce": "Ounces (oz)",
    "pound": "Pounds (lb)",
    "celsius": "Celsius (°C)",
    "fahrenheit": "Fahrenheit (°F)",
    "kelvin": "Kelvin (K)",
    "square_meter": "Square meters (m²)",
    "square_kilometer": "Square kilometers (km²)",
    "square_foot": "Square feet (ft²)",
    "acre": "Acres",
    "hectare": "Hectares",
    "milliliter": "Milliliters (mL)",
    "liter": "Liters (L)",
    "cubic_meter": "Cubic meters (m³)",
    "gallon_us": "Gallons (US)",
    "quart_us": "Quarts (US)",
    "cup_us": "Cups (US)",
    "meters_per_second": "Meters/second (m/s)",
    "kilometers_per_hour": "Kilometers/hour (km/h)",
    "miles_per_hour": "Miles/hour (mph)",
    "second": "Seconds",
    "minute": "Minutes",
    "hour": "Hours",
    "day": "Days",
    "week": "Weeks",
    "byte": "Bytes (decimal)",
    "kilobyte": "Kilobytes, KB (1000 B)",
    "megabyte": "Megabytes, MB (1000² B)",
    "gigabyte": "Gigabytes, GB (1000³ B)",
    "terabyte": "Terabytes, TB (1000⁴ B)",
    "kibibyte": "Kibibytes, KiB (1024 B)",
    "mebibyte": "Mebibytes, MiB (1024² B)",
    "gibibyte": "Gibibytes, GiB (1024³ B)",
    "tebibyte": "Tebibytes, TiB (1024⁴ B)",
}


def _units_for(category: str):
    if category == "temperature":
        return list(_TEMPERATURE_UNITS)
    return list(CATEGORIES[category].keys())


class ConverterView(tk.Frame):
    def __init__(self, parent, colors, on_status=None):
        super().__init__(parent, bg=colors["background"])
        self.colors = colors
        self.on_status = on_status or (lambda text: None)
        self._build()

    def _build(self):
        c = self.colors
        pad = {"padx": 16, "pady": 8}

        section_label(self, "Convert", c, size=16).pack(anchor="w", **pad)

        form = tk.Frame(self, bg=c["background"])
        form.pack(fill="x", padx=16)

        section_label(form, "Category", c).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.category_var = tk.StringVar(value="length")
        category_box = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=list(_CATEGORY_LABELS.keys()),
            state="readonly",
            style="Cinqic.TCombobox",
        )
        category_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        category_box.bind("<<ComboboxSelected>>", self._on_category_change)

        section_label(form, "From", c).grid(row=2, column=0, sticky="w")
        section_label(form, "To", c).grid(row=2, column=1, sticky="w")

        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()
        self.from_box = ttk.Combobox(form, textvariable=self.from_var, state="readonly", style="Cinqic.TCombobox")
        self.to_box = ttk.Combobox(form, textvariable=self.to_var, state="readonly", style="Cinqic.TCombobox")
        self.from_box.grid(row=3, column=0, sticky="ew", padx=(0, 6), pady=(0, 12))
        self.to_box.grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(0, 12))
        self.from_box.bind("<<ComboboxSelected>>", lambda e: self._recalculate())
        self.to_box.bind("<<ComboboxSelected>>", lambda e: self._recalculate())

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        section_label(form, "Value", c).grid(row=4, column=0, sticky="w")
        self.value_var = tk.StringVar(value="1")
        value_entry = styled_entry(form, c, textvariable=self.value_var, width=20)
        value_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        value_entry.bind("<KeyRelease>", lambda e: self._recalculate())

        result_frame = tk.Frame(self, bg=c["panel"], highlightbackground=c["border"], highlightthickness=1)
        result_frame.pack(fill="x", padx=16, pady=(0, 16))
        section_label(result_frame, "Result", c).pack(anchor="w", padx=12, pady=(10, 0))
        self.result_var = tk.StringVar(value="")
        tk.Label(
            result_frame,
            textvariable=self.result_var,
            font=("Segoe UI", 20),
            bg=c["panel"],
            fg=c["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 10))

        self.note_var = tk.StringVar(value="")
        tk.Label(
            self,
            textvariable=self.note_var,
            font=("Segoe UI", 9),
            bg=c["background"],
            fg=c["text_secondary"],
            anchor="w",
            wraplength=380,
            justify="left",
        ).pack(fill="x", padx=16)

        self._on_category_change()

    def _on_category_change(self, _event=None):
        category = self.category_var.get()
        units = _units_for(category)
        labels = [_UNIT_LABELS.get(u, u) for u in units]
        self._unit_by_label = dict(zip(labels, units))
        self.from_box["values"] = labels
        self.to_box["values"] = labels
        if labels:
            self.from_var.set(labels[0])
            self.to_var.set(labels[1] if len(labels) > 1 else labels[0])
        if category == "data_storage":
            self.note_var.set(
                "Decimal units (KB, MB, GB...) use base 1000. Binary units "
                "(KiB, MiB, GiB...) use base 1024. They are not the same."
            )
        else:
            self.note_var.set("")
        self._recalculate()

    def _recalculate(self, _event=None):
        category = self.category_var.get()
        from_label = self.from_var.get()
        to_label = self.to_var.get()
        from_unit = self._unit_by_label.get(from_label)
        to_unit = self._unit_by_label.get(to_label)
        if from_unit is None or to_unit is None:
            return
        try:
            value = float(self.value_var.get())
        except ValueError:
            self.result_var.set("Enter a valid number")
            return
        try:
            result = convert(category, from_unit, to_unit, value)
        except ConversionError as exc:
            self.result_var.set(f"Error: {exc}")
            return
        self.result_var.set(_format_result(result))
        self.on_status("Conversion updated")


def _format_result(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
