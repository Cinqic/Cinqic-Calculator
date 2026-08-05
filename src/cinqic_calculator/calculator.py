"""Core calculator state machine: standard arithmetic, scientific functions,
and memory. UI-independent and fully unit-testable.
"""

import math

MAX_DIGITS = 15
_ERROR = "Error"


class Calculator:
    """Tracks display/expression state and turns button presses into results."""

    def __init__(self):
        self.display = "0"
        self.expression = ""
        self.stored_value = None
        self.pending_operator = None
        self.start_fresh = True
        self.degree_mode = True
        self.memory = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def clear_all(self):
        self._reset_state()

    def _reset_state(self):
        self.display = "0"
        self.expression = ""
        self.stored_value = None
        self.pending_operator = None
        self.start_fresh = True

    def clear_entry(self):
        self.display = "0"
        self.start_fresh = True

    def backspace(self):
        if self.display == _ERROR or self.start_fresh:
            self.clear_entry()
            return
        if len(self.display) <= 1 or (len(self.display) == 2 and self.display.startswith("-")):
            self.display = "0"
            self.start_fresh = True
        else:
            self.display = self.display[:-1]

    def input_digit(self, digit: str):
        if self.display == _ERROR:
            self._reset_state()
        if self.start_fresh:
            self.display = digit
            self.start_fresh = False
        elif self.display == "0":
            self.display = digit
        elif len(self.display.replace("-", "").replace(".", "")) < MAX_DIGITS:
            self.display += digit

    def input_decimal(self):
        if self.display == _ERROR:
            self._reset_state()
        if self.start_fresh:
            self.display = "0."
            self.start_fresh = False
        elif "." not in self.display:
            self.display += "."

    def toggle_sign(self):
        if self.display == _ERROR:
            return
        if self.display.startswith("-"):
            self.display = self.display[1:]
        elif self.display != "0":
            self.display = "-" + self.display

    def percent(self):
        if self.display == _ERROR:
            return
        try:
            value = float(self.display)
        except ValueError:
            self.display = _ERROR
            return
        if self.pending_operator and self.stored_value is not None:
            value = self.stored_value * (value / 100)
        else:
            value = value / 100
        self.display = self._format(value)
        self.start_fresh = True

    def set_operator(self, operator_symbol: str):
        if self.display == _ERROR:
            return
        if self.pending_operator and not self.start_fresh:
            self._equals()
            if self.display == _ERROR:
                return
        try:
            self.stored_value = float(self.display)
        except ValueError:
            self.display = _ERROR
            return
        self.pending_operator = operator_symbol
        self.start_fresh = True

    def equals(self):
        if self.display == _ERROR:
            return
        self._equals()

    def _equals(self):
        if self.pending_operator is None or self.stored_value is None:
            return
        try:
            second_value = float(self.display)
        except ValueError:
            self.display = _ERROR
            return
        try:
            result = _apply_operator(self.stored_value, second_value, self.pending_operator)
        except ZeroDivisionError:
            self.display = _ERROR
            self.pending_operator = None
            self.stored_value = None
            self.start_fresh = True
            return
        self.display = self._format(result)
        self.stored_value = None
        self.pending_operator = None
        self.start_fresh = True

    # -- Scientific -----------------------------------------------------
    def apply_unary(self, name: str):
        """Apply a scientific unary function to the current display value."""
        if self.display == _ERROR:
            return
        try:
            value = float(self.display)
        except ValueError:
            self.display = _ERROR
            return
        try:
            result = _SCIENTIFIC_FUNCTIONS[name](value, self.degree_mode)
        except KeyError:
            raise ValueError(f"Unknown scientific function: {name}") from None
        except (ValueError, OverflowError, ZeroDivisionError):
            self.display = _ERROR
            self.start_fresh = True
            return
        self.display = self._format(result)
        self.start_fresh = True

    def insert_constant(self, name: str):
        if name == "pi":
            self.display = self._format(math.pi)
        elif name == "e":
            self.display = self._format(math.e)
        else:
            raise ValueError(f"Unknown constant: {name}")
        self.start_fresh = True

    def set_degree_mode(self, degrees: bool):
        self.degree_mode = degrees

    # -- Memory -----------------------------------------------------------
    def memory_clear(self):
        self.memory = None

    def memory_recall(self):
        if self.memory is not None:
            self.display = self._format(self.memory)
            self.start_fresh = True

    def memory_add(self):
        try:
            value = float(self.display)
        except ValueError:
            return
        self.memory = (self.memory or 0.0) + value

    def memory_subtract(self):
        try:
            value = float(self.display)
        except ValueError:
            return
        self.memory = (self.memory or 0.0) - value

    def memory_store(self):
        try:
            self.memory = float(self.display)
        except ValueError:
            pass

    @property
    def has_memory(self) -> bool:
        return self.memory is not None

    # -- Formatting -------------------------------------------------------
    @staticmethod
    def _format(number: float) -> str:
        if number != number or math.isinf(number):  # NaN or infinity
            return _ERROR
        if number == int(number) and abs(number) < 1e15:
            return str(int(number))
        text = f"{number:.10f}".rstrip("0").rstrip(".")
        return text if text else "0"


def _apply_operator(first: float, second: float, operator_symbol: str) -> float:
    if operator_symbol == "+":
        return first + second
    if operator_symbol == "-":
        return first - second
    if operator_symbol in ("*", "×"):
        return first * second
    if operator_symbol in ("/", "÷"):
        if second == 0:
            raise ZeroDivisionError
        return first / second
    raise ValueError(f"Unknown operator: {operator_symbol}")


def _sci_square(value, _degrees):
    return value**2


def _sci_cube(value, _degrees):
    return value**3


def _sci_sqrt(value, _degrees):
    if value < 0:
        raise ValueError("sqrt of negative number")
    return math.sqrt(value)


def _sci_cbrt(value, _degrees):
    return math.copysign(abs(value) ** (1 / 3), value)


def _sci_reciprocal(value, _degrees):
    if value == 0:
        raise ZeroDivisionError
    return 1.0 / value


def _sci_factorial(value, _degrees):
    if value < 0 or value != int(value):
        raise ValueError("factorial requires a non-negative integer")
    if value > 170:
        raise OverflowError("factorial too large")
    return float(math.factorial(int(value)))


def _sci_abs(value, _degrees):
    return abs(value)


def _sci_ln(value, _degrees):
    if value <= 0:
        raise ValueError("ln requires a positive number")
    return math.log(value)


def _sci_log10(value, _degrees):
    if value <= 0:
        raise ValueError("log requires a positive number")
    return math.log10(value)


def _to_radians(value, degrees):
    return math.radians(value) if degrees else value


def _sci_sin(value, degrees):
    return math.sin(_to_radians(value, degrees))


def _sci_cos(value, degrees):
    return math.cos(_to_radians(value, degrees))


def _sci_tan(value, degrees):
    radians = _to_radians(value, degrees)
    cosine = math.cos(radians)
    if abs(cosine) < 1e-12:
        raise ValueError("tangent undefined at this value")
    return math.tan(radians)


_SCIENTIFIC_FUNCTIONS = {
    "square": _sci_square,
    "cube": _sci_cube,
    "sqrt": _sci_sqrt,
    "cbrt": _sci_cbrt,
    "reciprocal": _sci_reciprocal,
    "factorial": _sci_factorial,
    "abs": _sci_abs,
    "ln": _sci_ln,
    "log10": _sci_log10,
    "sin": _sci_sin,
    "cos": _sci_cos,
    "tan": _sci_tan,
}
