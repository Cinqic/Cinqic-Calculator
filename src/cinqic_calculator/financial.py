"""Practical percentage, pricing, and interest tools.

Currency-oriented math uses decimal.Decimal internally for accuracy and
rounds only for display. All results here are estimates, not financial,
tax, or investment advice, and growth is never guaranteed.
"""

from decimal import ROUND_HALF_UP, Decimal

__all__ = [
    "percentage_of",
    "percentage_increase",
    "percentage_decrease",
    "percentage_difference",
    "discount",
    "sales_tax",
    "final_price",
    "tip",
    "split_bill",
    "simple_interest",
    "compound_interest",
]

TWO_PLACES = Decimal("0.01")


def _d(value) -> Decimal:
    return Decimal(str(value))


def _round_currency(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Percentage tools
# ---------------------------------------------------------------------------
def percentage_of(number, percent) -> float:
    return float(_d(number) * _d(percent) / Decimal(100))


def percentage_increase(number, percent) -> float:
    return float(_d(number) * (Decimal(1) + _d(percent) / Decimal(100)))


def percentage_decrease(number, percent) -> float:
    return float(_d(number) * (Decimal(1) - _d(percent) / Decimal(100)))


def percentage_difference(old_value, new_value) -> float:
    old_d = _d(old_value)
    if old_d == 0:
        raise ValueError("Cannot compute percentage difference from zero")
    return float((_d(new_value) - old_d) / abs(old_d) * Decimal(100))


# ---------------------------------------------------------------------------
# Price tools
# ---------------------------------------------------------------------------
def discount(price, percent) -> float:
    result = _d(price) * (Decimal(1) - _d(percent) / Decimal(100))
    return float(_round_currency(result))


def sales_tax(price, tax_rate_percent) -> float:
    result = _d(price) * _d(tax_rate_percent) / Decimal(100)
    return float(_round_currency(result))


def final_price(price, discount_percent=0, tax_rate_percent=0) -> float:
    discounted = _d(price) * (Decimal(1) - _d(discount_percent) / Decimal(100))
    taxed = discounted * (Decimal(1) + _d(tax_rate_percent) / Decimal(100))
    return float(_round_currency(taxed))


def tip(bill_total, tip_percent) -> float:
    result = _d(bill_total) * _d(tip_percent) / Decimal(100)
    return float(_round_currency(result))


def split_bill(bill_total, num_people, tip_percent=0) -> float:
    if num_people <= 0:
        raise ValueError("Number of people must be positive")
    total_with_tip = _d(bill_total) * (Decimal(1) + _d(tip_percent) / Decimal(100))
    per_person = total_with_tip / Decimal(num_people)
    return float(_round_currency(per_person))


# ---------------------------------------------------------------------------
# Interest tools
# ---------------------------------------------------------------------------
def simple_interest(principal, annual_rate_percent, years) -> float:
    interest = _d(principal) * _d(annual_rate_percent) / Decimal(100) * _d(years)
    return float(_round_currency(interest))


def compound_interest(principal, annual_rate_percent, years, compounds_per_year=1) -> float:
    """Return the total value (principal + compounded interest) as an estimate."""
    if compounds_per_year <= 0:
        raise ValueError("Compounding frequency must be positive")
    rate = float(annual_rate_percent) / 100.0
    n = float(compounds_per_year)
    t = float(years)
    growth = (1.0 + rate / n) ** (n * t)
    total = _d(principal) * _d(growth)
    return float(_round_currency(total))
