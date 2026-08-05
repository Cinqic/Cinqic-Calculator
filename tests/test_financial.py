import pytest

from cinqic_calculator.financial import (
    compound_interest,
    discount,
    final_price,
    percentage_decrease,
    percentage_difference,
    percentage_increase,
    percentage_of,
    sales_tax,
    simple_interest,
    split_bill,
    tip,
)


def test_percentage_of():
    assert percentage_of(200, 10) == 20


def test_percentage_increase():
    assert percentage_increase(100, 20) == 120


def test_percentage_decrease():
    assert percentage_decrease(100, 20) == 80


def test_percentage_difference():
    assert percentage_difference(50, 75) == pytest.approx(50)


def test_percentage_difference_zero_base_raises():
    with pytest.raises(ValueError):
        percentage_difference(0, 10)


def test_discount():
    assert discount(100, 25) == 75.0


def test_sales_tax():
    assert sales_tax(100, 8.5) == 8.5


def test_final_price_discount_and_tax():
    # 100 -> 90 after 10% discount -> 97.20 after 8% tax
    assert final_price(100, discount_percent=10, tax_rate_percent=8) == pytest.approx(97.20)


def test_tip_calculation():
    assert tip(50, 20) == 10.0


def test_split_bill_no_tip():
    assert split_bill(100, 4) == 25.0


def test_split_bill_with_tip():
    assert split_bill(100, 4, tip_percent=10) == 27.5


def test_split_bill_zero_people_raises():
    with pytest.raises(ValueError):
        split_bill(100, 0)


def test_simple_interest():
    assert simple_interest(1000, 5, 2) == 100.0


def test_compound_interest_annual():
    result = compound_interest(1000, 5, 1, compounds_per_year=1)
    assert result == pytest.approx(1050.0, rel=1e-3)


def test_compound_interest_monthly():
    result = compound_interest(1000, 12, 1, compounds_per_year=12)
    assert result == pytest.approx(1126.83, rel=1e-3)


def test_compound_interest_zero_frequency_raises():
    with pytest.raises(ValueError):
        compound_interest(1000, 5, 1, compounds_per_year=0)


def test_currency_rounding_two_decimal_places():
    result = sales_tax(19.99, 7.25)
    text = f"{result:.2f}"
    assert text == f"{result}" or round(result, 2) == result
