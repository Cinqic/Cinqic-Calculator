import pytest

from cinqic_calculator.calculator import Calculator


def press_digits(calc, text):
    for ch in text:
        if ch == ".":
            calc.input_decimal()
        else:
            calc.input_digit(ch)


def test_addition():
    calc = Calculator()
    press_digits(calc, "5")
    calc.set_operator("+")
    press_digits(calc, "3")
    calc.equals()
    assert calc.display == "8"


def test_subtraction():
    calc = Calculator()
    press_digits(calc, "10")
    calc.set_operator("-")
    press_digits(calc, "4")
    calc.equals()
    assert calc.display == "6"


def test_multiplication():
    calc = Calculator()
    press_digits(calc, "6")
    calc.set_operator("*")
    press_digits(calc, "7")
    calc.equals()
    assert calc.display == "42"


def test_division():
    calc = Calculator()
    press_digits(calc, "9")
    calc.set_operator("/")
    press_digits(calc, "2")
    calc.equals()
    assert calc.display == "4.5"


def test_division_by_zero():
    calc = Calculator()
    press_digits(calc, "5")
    calc.set_operator("/")
    press_digits(calc, "0")
    calc.equals()
    assert calc.display == "Error"


def test_negative_values():
    calc = Calculator()
    press_digits(calc, "5")
    calc.toggle_sign()
    assert calc.display == "-5"
    calc.set_operator("+")
    press_digits(calc, "3")
    calc.equals()
    assert calc.display == "-2"


def test_decimal_input():
    calc = Calculator()
    press_digits(calc, "3.14")
    assert calc.display == "3.14"


def test_repeated_decimal_ignored():
    calc = Calculator()
    press_digits(calc, "3.1.4")
    assert calc.display == "3.14"


def test_percent_standalone():
    calc = Calculator()
    press_digits(calc, "50")
    calc.percent()
    assert calc.display == "0.5"


def test_percent_of_stored_value():
    calc = Calculator()
    press_digits(calc, "200")
    calc.set_operator("+")
    press_digits(calc, "10")
    calc.percent()
    assert calc.display == "20"


def test_clear_entry():
    calc = Calculator()
    press_digits(calc, "42")
    calc.clear_entry()
    assert calc.display == "0"


def test_clear_all():
    calc = Calculator()
    press_digits(calc, "5")
    calc.set_operator("+")
    press_digits(calc, "3")
    calc.clear_all()
    assert calc.display == "0"
    assert calc.pending_operator is None
    assert calc.stored_value is None


def test_backspace():
    calc = Calculator()
    press_digits(calc, "123")
    calc.backspace()
    assert calc.display == "12"


def test_backspace_to_zero():
    calc = Calculator()
    press_digits(calc, "5")
    calc.backspace()
    assert calc.display == "0"


def test_repeated_equals():
    calc = Calculator()
    press_digits(calc, "5")
    calc.set_operator("+")
    press_digits(calc, "3")
    calc.equals()
    assert calc.display == "8"


def test_invalid_expression_after_error_resets():
    calc = Calculator()
    press_digits(calc, "5")
    calc.set_operator("/")
    press_digits(calc, "0")
    calc.equals()
    assert calc.display == "Error"
    calc.input_digit("7")
    assert calc.display == "7"


# ---------------------------------------------------------------------------
# Scientific functions
# ---------------------------------------------------------------------------
def test_square():
    calc = Calculator()
    press_digits(calc, "4")
    calc.apply_unary("square")
    assert calc.display == "16"


def test_cube():
    calc = Calculator()
    press_digits(calc, "3")
    calc.apply_unary("cube")
    assert calc.display == "27"


def test_sqrt_negative_is_error():
    calc = Calculator()
    press_digits(calc, "9")
    calc.toggle_sign()
    calc.apply_unary("sqrt")
    assert calc.display == "Error"


def test_reciprocal():
    calc = Calculator()
    press_digits(calc, "4")
    calc.apply_unary("reciprocal")
    assert calc.display == "0.25"


def test_reciprocal_of_zero_is_error():
    calc = Calculator()
    calc.apply_unary("reciprocal")
    assert calc.display == "Error"


def test_factorial():
    calc = Calculator()
    press_digits(calc, "5")
    calc.apply_unary("factorial")
    assert calc.display == "120"


def test_factorial_of_negative_is_error():
    calc = Calculator()
    press_digits(calc, "3")
    calc.toggle_sign()
    calc.apply_unary("factorial")
    assert calc.display == "Error"


def test_factorial_of_non_integer_is_error():
    calc = Calculator()
    press_digits(calc, "3.5")
    calc.apply_unary("factorial")
    assert calc.display == "Error"


def test_log_of_zero_is_error():
    calc = Calculator()
    press_digits(calc, "0")
    calc.apply_unary("log10")
    assert calc.display == "Error"


def test_log_of_negative_is_error():
    calc = Calculator()
    press_digits(calc, "5")
    calc.toggle_sign()
    calc.apply_unary("ln")
    assert calc.display == "Error"


def test_tangent_undefined_is_error():
    calc = Calculator()
    calc.set_degree_mode(True)
    press_digits(calc, "90")
    calc.apply_unary("tan")
    assert calc.display == "Error"


def test_sin_degree_mode():
    calc = Calculator()
    calc.set_degree_mode(True)
    press_digits(calc, "90")
    calc.apply_unary("sin")
    assert calc.display == "1"


def test_sin_radian_mode():
    calc = Calculator()
    calc.set_degree_mode(False)
    press_digits(calc, "0")
    calc.apply_unary("sin")
    assert calc.display == "0"


def test_pi_constant():
    calc = Calculator()
    calc.insert_constant("pi")
    assert calc.display.startswith("3.14159")


def test_e_constant():
    calc = Calculator()
    calc.insert_constant("e")
    assert calc.display.startswith("2.71828")


def test_absolute_value():
    calc = Calculator()
    press_digits(calc, "7")
    calc.toggle_sign()
    calc.apply_unary("abs")
    assert calc.display == "7"


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------
def test_memory_store_and_recall():
    calc = Calculator()
    press_digits(calc, "42")
    calc.memory_store()
    assert calc.has_memory
    calc.clear_entry()
    calc.memory_recall()
    assert calc.display == "42"


def test_memory_add_and_subtract():
    calc = Calculator()
    press_digits(calc, "10")
    calc.memory_store()
    calc.clear_entry()
    press_digits(calc, "5")
    calc.memory_add()
    calc.clear_entry()
    calc.memory_recall()
    assert calc.display == "15"

    calc.clear_entry()
    press_digits(calc, "3")
    calc.memory_subtract()
    calc.clear_entry()
    calc.memory_recall()
    assert calc.display == "12"


def test_memory_clear():
    calc = Calculator()
    press_digits(calc, "5")
    calc.memory_store()
    assert calc.has_memory
    calc.memory_clear()
    assert not calc.has_memory
