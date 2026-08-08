"""Unit conversion screen: category + from/to unit spinners, live output."""

from __future__ import annotations

from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from cinqic_calculator import conversions

_TEMPERATURE_UNITS = ["celsius", "fahrenheit", "kelvin"]


class ConvertScreen(Screen):
    result_text = StringProperty("")

    # -- Category / unit population ---------------------------------------
    @staticmethod
    def get_categories() -> list:
        # conversions.CATEGORIES covers length/mass/area/volume/speed/time/
        # data_storage; temperature is handled by convert_temperature() and
        # is not a key in CATEGORIES since it isn't a simple scale factor,
        # so it's appended here explicitly per the module's own docstring.
        return [*conversions.CATEGORIES.keys(), "temperature"]

    @staticmethod
    def get_units(category: str) -> list:
        if category == "temperature":
            return list(_TEMPERATURE_UNITS)
        table = conversions.CATEGORIES.get(category, {})
        return list(table.keys())

    def on_pre_enter(self, *_args):
        categories = self.get_categories()
        self.ids.category_spinner.values = categories
        if self.ids.category_spinner.text not in categories:
            self.ids.category_spinner.text = categories[0]
        self._refresh_unit_spinners()

    def on_category_selected(self, _category: str):
        self._refresh_unit_spinners()
        self.convert()

    def _refresh_unit_spinners(self):
        category = self.ids.category_spinner.text
        units = self.get_units(category)
        self.ids.from_spinner.values = units
        self.ids.to_spinner.values = units
        if self.ids.from_spinner.text not in units:
            self.ids.from_spinner.text = units[0]
        if self.ids.to_spinner.text not in units:
            self.ids.to_spinner.text = units[1] if len(units) > 1 else units[0]

    def swap_units(self):
        self.ids.from_spinner.text, self.ids.to_spinner.text = (
            self.ids.to_spinner.text,
            self.ids.from_spinner.text,
        )
        self.convert()

    # -- Conversion ---------------------------------------------------------
    def convert(self):
        category = self.ids.category_spinner.text
        from_unit = self.ids.from_spinner.text
        to_unit = self.ids.to_spinner.text
        raw_value = self.ids.value_input.text.strip()
        if not raw_value:
            self.result_text = ""
            return
        try:
            value = float(raw_value)
        except ValueError:
            self.result_text = "Invalid input"
            return
        try:
            result = conversions.convert(category, from_unit, to_unit, value)
        except conversions.ConversionError:
            self.result_text = "Invalid units"
            return
        self.result_text = _format_number(result)


def _format_number(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text if text else "0"
