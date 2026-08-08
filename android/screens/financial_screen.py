"""Financial calculator screen: one spinner selects the operation, up to
four labeled input fields (some optional) feed the matching financial.py
function, and the result is shown formatted for its kind (currency vs. a
plain percentage/number).
"""

from __future__ import annotations

from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

from cinqic_calculator import financial


def _currency(value: float) -> str:
    return f"${value:.2f}"


def _plain_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _percent(value: float) -> str:
    return f"{value:.2f}%"


# Each entry: fields = list of (kwarg_name, label, optional) in the exact
# positional order financial.py expects; func = the financial.py callable;
# format = how to render the numeric result.
OPERATIONS = {
    "Percentage of": {
        "fields": [("number", "Number", False), ("percent", "Percent", False)],
        "func": financial.percentage_of,
        "format": _plain_number,
    },
    "Percentage increase": {
        "fields": [("number", "Number", False), ("percent", "Increase %", False)],
        "func": financial.percentage_increase,
        "format": _plain_number,
    },
    "Percentage decrease": {
        "fields": [("number", "Number", False), ("percent", "Decrease %", False)],
        "func": financial.percentage_decrease,
        "format": _plain_number,
    },
    "Percentage difference": {
        "fields": [("old_value", "Old value", False), ("new_value", "New value", False)],
        "func": financial.percentage_difference,
        "format": _percent,
    },
    "Discount": {
        "fields": [("price", "Price", False), ("percent", "Discount %", False)],
        "func": financial.discount,
        "format": _currency,
    },
    "Sales tax": {
        "fields": [("price", "Price", False), ("tax_rate_percent", "Tax rate %", False)],
        "func": financial.sales_tax,
        "format": _currency,
    },
    "Final price": {
        "fields": [
            ("price", "Price", False),
            ("discount_percent", "Discount %", True),
            ("tax_rate_percent", "Tax rate %", True),
        ],
        "func": financial.final_price,
        "format": _currency,
    },
    "Tip": {
        "fields": [("bill_total", "Bill total", False), ("tip_percent", "Tip %", False)],
        "func": financial.tip,
        "format": _currency,
    },
    "Split bill": {
        "fields": [
            ("bill_total", "Bill total", False),
            ("num_people", "Number of people", False),
            ("tip_percent", "Tip %", True),
        ],
        "func": financial.split_bill,
        "format": _currency,
    },
    "Simple interest": {
        "fields": [
            ("principal", "Principal", False),
            ("annual_rate_percent", "Annual rate %", False),
            ("years", "Years", False),
        ],
        "func": financial.simple_interest,
        "format": _currency,
    },
    "Compound interest": {
        "fields": [
            ("principal", "Principal", False),
            ("annual_rate_percent", "Annual rate %", False),
            ("years", "Years", False),
            ("compounds_per_year", "Compounds per year", True),
        ],
        "func": financial.compound_interest,
        "format": _currency,
    },
}

_MAX_FIELDS = 4


class FinancialScreen(Screen):
    operation_names = ListProperty(list(OPERATIONS.keys()))
    result_text = StringProperty("")
    field_labels = ListProperty(["", "", "", ""])
    field_visible = ListProperty([False, False, False, False])

    def on_pre_enter(self, *_args):
        if self.ids.operation_spinner.text not in OPERATIONS:
            self.ids.operation_spinner.text = self.operation_names[0]
        self._refresh_fields()

    def on_operation_selected(self, _name: str):
        self._refresh_fields()
        self.result_text = ""

    def _field_inputs(self):
        return [self.ids.field1, self.ids.field2, self.ids.field3, self.ids.field4]

    def _refresh_fields(self):
        op = OPERATIONS[self.ids.operation_spinner.text]
        fields = op["fields"]
        labels = [""] * _MAX_FIELDS
        visible = [False] * _MAX_FIELDS
        for index, (_key, label, optional) in enumerate(fields):
            labels[index] = f"{label} (optional)" if optional else label
            visible[index] = True
        inputs = self._field_inputs()
        for index, widget in enumerate(inputs):
            if not visible[index]:
                widget.text = ""
        self.field_labels = labels
        self.field_visible = visible
        # Bug fix: switching to an operation with fewer visible fields
        # while scrolled down left the ScrollView's content clipped above
        # the viewport instead of snapping back to show the (now shorter)
        # form from the top. field_visible's kv bindings (see
        # financial.kv) update field heights immediately, but the
        # ScrollView's own scroll_y is a fraction of total content height
        # and does not automatically renormalize when that height shrinks
        # until Kivy's own layout pass has actually recomputed
        # minimum_height -- one frame later. Scheduling the reset via
        # Clock.schedule_once(..., 0), rather than setting scroll_y
        # immediately here, is what makes it apply after that recompute
        # instead of before it (setting it here would just get overwritten
        # by the pending layout pass). See calculator_screen.py's
        # _schedule_relayout()/_force_relayout() for the equivalent fix on
        # a screen that has no ScrollView.
        Clock.schedule_once(self._reset_scroll, 0)

    def _reset_scroll(self, _dt):
        scroll_view = self.ids.get("scroll_view")
        if scroll_view is not None:
            scroll_view.scroll_y = 1

    def calculate(self):
        op_name = self.ids.operation_spinner.text
        op = OPERATIONS.get(op_name)
        if op is None:
            return

        inputs = self._field_inputs()
        args = []
        try:
            for index, (_key, _label, optional) in enumerate(op["fields"]):
                raw = inputs[index].text.strip()
                if not raw:
                    if optional:
                        continue
                    self.result_text = "Missing input"
                    return
                args.append(float(raw))
        except ValueError:
            self.result_text = "Invalid input"
            return

        try:
            result = op["func"](*args)
        except (ValueError, ZeroDivisionError, ArithmeticError) as exc:
            self.result_text = str(exc) or "Invalid input"
            return

        self.result_text = op["format"](result)
