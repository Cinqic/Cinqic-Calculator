"""Cinqic Calculator

A clean, working desktop calculator built with tkinter, styled after modern
iPhone calculators: black background, dark number keys, light gray function
keys, and green operator keys.
"""

import math
import tkinter

# ---------------------------------------------------------------------------
# Button layout
# ---------------------------------------------------------------------------
BUTTON_VALUES = [
    ["AC", "+/-", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "-"],
    ["1", "2", "3", "+"],
    ["0", ".", "√", "="],
]

FUNCTION_SYMBOLS = ["AC", "+/-", "%"]
OPERATOR_SYMBOLS = ["÷", "×", "-", "+", "="]

ROW_COUNT = len(BUTTON_VALUES)
COLUMN_COUNT = len(BUTTON_VALUES[0])

# ---------------------------------------------------------------------------
# Colors - black background with green accents (Cinqic theme)
# ---------------------------------------------------------------------------
COLOR_BACKGROUND = "#000000"
COLOR_DISPLAY_TEXT = "#FFFFFF"

COLOR_NUMBER_BG = "#333333"
COLOR_NUMBER_ACTIVE_BG = "#4D4D4D"
COLOR_NUMBER_TEXT = "#FFFFFF"

COLOR_FUNCTION_BG = "#A5A5A5"
COLOR_FUNCTION_ACTIVE_BG = "#D9D9D9"
COLOR_FUNCTION_TEXT = "#000000"

COLOR_OPERATOR_BG = "#32CD32"
COLOR_OPERATOR_ACTIVE_BG = "#28A428"
COLOR_OPERATOR_TEXT = "#FFFFFF"


# ---------------------------------------------------------------------------
# Calculation engine - plain Python, no tkinter dependency, fully testable
# ---------------------------------------------------------------------------
class CalculatorLogic:
    """Tracks calculator state and turns button presses into a display value."""

    MAX_DIGITS = 9

    def __init__(self):
        self.display = "0"
        self.stored_value = None
        self.pending_operator = None
        self.start_fresh = True

    def reset(self):
        self.__init__()

    def press(self, value):
        """Process one button press and return the new display string."""
        if self.display == "Error" and value != "AC":
            self.reset()

        if value == "AC":
            self.reset()
        elif value == "+/-":
            self._toggle_sign()
        elif value == "%":
            self._percent()
        elif value == "√":
            self._square_root()
        elif value == ".":
            self._input_decimal()
        elif value in ("÷", "×", "-", "+"):
            self._set_operator(value)
        elif value == "=":
            self._equals()
        elif value.isdigit():
            self._input_digit(value)

        return self.display

    def _input_digit(self, digit):
        if self.start_fresh:
            self.display = digit
            self.start_fresh = False
        elif self.display == "0":
            self.display = digit
        elif len(self.display.replace("-", "").replace(".", "")) < self.MAX_DIGITS:
            self.display += digit

    def _input_decimal(self):
        if self.start_fresh:
            self.display = "0."
            self.start_fresh = False
        elif "." not in self.display:
            self.display += "."

    def _toggle_sign(self):
        if self.display.startswith("-"):
            self.display = self.display[1:]
        elif self.display != "0":
            self.display = "-" + self.display

    def _percent(self):
        self.display = self._format(float(self.display) / 100)
        self.start_fresh = True

    def _square_root(self):
        value = float(self.display)
        if value < 0:
            self.display = "Error"
        else:
            self.display = self._format(math.sqrt(value))
        self.start_fresh = True

    def _set_operator(self, operator_symbol):
        if self.pending_operator and not self.start_fresh:
            self._equals()
        self.stored_value = float(self.display)
        self.pending_operator = operator_symbol
        self.start_fresh = True

    def _equals(self):
        if self.pending_operator is None or self.stored_value is None:
            return
        second_value = float(self.display)
        result = self._calculate(self.stored_value, second_value, self.pending_operator)
        self.display = self._format(result)
        self.stored_value = None
        self.pending_operator = None
        self.start_fresh = True

    @staticmethod
    def _calculate(first_value, second_value, operator_symbol):
        if operator_symbol == "+":
            return first_value + second_value
        if operator_symbol == "-":
            return first_value - second_value
        if operator_symbol == "×":
            return first_value * second_value
        if operator_symbol == "÷":
            if second_value == 0:
                return float("nan")
            return first_value / second_value
        return second_value

    @staticmethod
    def _format(number):
        if number != number:  # NaN result (e.g. divide by zero)
            return "Error"
        if number == int(number) and abs(number) < 1e15:
            return str(int(number))
        text = f"{number:.8f}".rstrip("0").rstrip(".")
        return text


# ---------------------------------------------------------------------------
# tkinter UI
# ---------------------------------------------------------------------------
def build_calculator_window():
    """Create the Cinqic Calculator window and wire up its buttons."""
    calculator = CalculatorLogic()

    window = tkinter.Tk()
    window.title("Cinqic Calculator")
    window.resizable(False, False)
    window.configure(bg=COLOR_BACKGROUND)

    frame = tkinter.Frame(window, bg=COLOR_BACKGROUND)

    label = tkinter.Label(
        frame,
        text=calculator.display,
        anchor="e",
        font=("Arial", 45),
        bg=COLOR_BACKGROUND,
        fg=COLOR_DISPLAY_TEXT,
        padx=20,
        pady=30,
    )
    label.grid(row=0, column=0, columnspan=COLUMN_COUNT, sticky="nsew")

    def button_click(value):
        calculator.press(value)
        label.config(text=calculator.display)

    for row in range(ROW_COUNT):
        for column in range(COLUMN_COUNT):
            value = BUTTON_VALUES[row][column]

            if value in FUNCTION_SYMBOLS:
                bg_color, fg_color, active_bg = (
                    COLOR_FUNCTION_BG,
                    COLOR_FUNCTION_TEXT,
                    COLOR_FUNCTION_ACTIVE_BG,
                )
            elif value in OPERATOR_SYMBOLS:
                bg_color, fg_color, active_bg = (
                    COLOR_OPERATOR_BG,
                    COLOR_OPERATOR_TEXT,
                    COLOR_OPERATOR_ACTIVE_BG,
                )
            else:
                bg_color, fg_color, active_bg = (
                    COLOR_NUMBER_BG,
                    COLOR_NUMBER_TEXT,
                    COLOR_NUMBER_ACTIVE_BG,
                )

            button = tkinter.Button(
                frame,
                text=value,
                font=("Arial", 26),
                width=COLUMN_COUNT - 1,
                height=1,
                bg=bg_color,
                fg=fg_color,
                activebackground=active_bg,
                activeforeground=fg_color,
                bd=0,
                relief="flat",
                command=lambda value=value: button_click(value),
            )
            button.grid(row=row + 1, column=column, padx=1, pady=1, sticky="nsew")

    frame.pack()
    return window


if __name__ == "__main__":
    calculator_window = build_calculator_window()
    calculator_window.mainloop()