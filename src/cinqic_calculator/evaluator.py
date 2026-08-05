"""Deterministic, sandboxed arithmetic expression evaluator.

Parses expressions with Python's ``ast`` module and walks only an explicit
allowlist of node types. Anything else (attribute access, calls to
non-whitelisted names, imports, subscripts, comprehensions, etc.) is rejected
before any evaluation happens. There is no ``eval``/``exec`` anywhere in this
module.
"""

import ast
import math

__all__ = ["EvaluationError", "evaluate"]


class EvaluationError(ValueError):
    """Raised for invalid, unsafe, or undefined expressions."""


_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: _safe_div(a, b),
    ast.Mod: lambda a, b: math.fmod(a, b) if b != 0 else _raise_div_zero(),
    ast.Pow: lambda a, b: _safe_pow(a, b),
    ast.FloorDiv: lambda a, b: a // b if b != 0 else _raise_div_zero(),
}

_UNARY_OPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

_ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
    "abs": abs,
    "log": math.log10,
    "ln": math.log,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "factorial": math.factorial,
    "reciprocal": lambda x: _safe_div(1.0, x),
}

_ALLOWED_NAMES = {
    "pi": math.pi,
    "e": math.e,
}


def _raise_div_zero():
    raise EvaluationError("Division by zero")


def _safe_div(a, b):
    if b == 0:
        _raise_div_zero()
    return a / b


def _safe_pow(a, b):
    try:
        result = a**b
    except OverflowError as exc:
        raise EvaluationError("Result too large") from exc
    if isinstance(result, complex):
        raise EvaluationError("Result is not a real number")
    return result


def evaluate(expression: str) -> float:
    """Evaluate a whitelisted arithmetic expression and return a float.

    Raises EvaluationError for empty, malformed, unsafe, or undefined input.
    """
    if not expression or not expression.strip():
        raise EvaluationError("Empty expression")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise EvaluationError("Invalid expression") from exc

    try:
        result = _eval_node(tree.body)
    except EvaluationError:
        raise
    except ZeroDivisionError as exc:
        raise EvaluationError("Division by zero") from exc
    except (ValueError, ArithmeticError) as exc:
        raise EvaluationError(str(exc)) from exc

    if isinstance(result, complex):
        raise EvaluationError("Result is not a real number")
    if isinstance(result, float) and (math.isnan(result) or math.isinf(result)):
        raise EvaluationError("Result is undefined")
    return float(result)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise EvaluationError("Only numeric literals are allowed")
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise EvaluationError("Operator not allowed")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _BIN_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise EvaluationError("Operator not allowed")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise EvaluationError(f"Unknown identifier: {node.id}")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EvaluationError("Unsupported call target")
        name = node.func.name if hasattr(node.func, "name") else node.func.id
        if name not in _ALLOWED_FUNCTIONS or node.keywords:
            raise EvaluationError(f"Function not allowed: {name}")
        args = [_eval_node(arg) for arg in node.args]
        try:
            return _ALLOWED_FUNCTIONS[name](*args)
        except (TypeError, ValueError) as exc:
            raise EvaluationError(str(exc)) from exc

    raise EvaluationError(f"Disallowed syntax: {type(node).__name__}")
