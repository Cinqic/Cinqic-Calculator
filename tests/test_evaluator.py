import math

import pytest

from cinqic_calculator.evaluator import EvaluationError, evaluate


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("1 + 2", 3),
        ("10 - 4", 6),
        ("3 * 4", 12),
        ("10 / 4", 2.5),
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4", 20),
        ("-5 + 2", -3),
        ("2 ** 3", 8),
        ("sqrt(16)", 4),
        ("abs(-7)", 7),
        ("pi", math.pi),
        ("e", math.e),
        ("sin(0)", 0),
        ("cos(0)", 1),
        ("factorial(5)", 120),
    ],
)
def test_valid_expressions(expression, expected):
    assert evaluate(expression) == pytest.approx(expected)


def test_division_by_zero_raises():
    with pytest.raises(EvaluationError):
        evaluate("1 / 0")


def test_empty_expression_raises():
    with pytest.raises(EvaluationError):
        evaluate("")
    with pytest.raises(EvaluationError):
        evaluate("   ")


def test_syntax_error_raises():
    with pytest.raises(EvaluationError):
        evaluate("2 +")
    with pytest.raises(EvaluationError):
        evaluate("(1 + 2")


@pytest.mark.parametrize(
    "malicious",
    [
        "__import__('os')",
        "__import__(\"os\").system(\"echo pwned\")",
        "open('file.txt')",
        "object.__subclasses__()",
        "().__class__",
        "[x for x in range(10)]",
        "lambda: 1",
        "1; 2",
        "exec('1')",
        "eval('1')",
        "globals()",
        "getattr(1, '__class__')",
    ],
)
def test_malicious_expressions_rejected(malicious):
    with pytest.raises(EvaluationError):
        evaluate(malicious)


def test_unknown_function_rejected():
    with pytest.raises(EvaluationError):
        evaluate("unknown_func(1)")


def test_unknown_name_rejected():
    with pytest.raises(EvaluationError):
        evaluate("undefined_name")


def test_complex_result_rejected():
    with pytest.raises(EvaluationError):
        evaluate("(-8) ** (1/3)")
