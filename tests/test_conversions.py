import pytest

from cinqic_calculator.conversions import ConversionError, convert, convert_temperature


def test_length_meters_to_feet():
    assert convert("length", "meter", "foot", 1) == pytest.approx(3.280839895, rel=1e-6)


def test_length_kilometers_to_miles():
    assert convert("length", "kilometer", "mile", 1) == pytest.approx(0.621371, rel=1e-4)


def test_mass_kilograms_to_pounds():
    assert convert("mass", "kilogram", "pound", 1) == pytest.approx(2.20462, rel=1e-4)


def test_area_square_meter_to_square_foot():
    assert convert("area", "square_meter", "square_foot", 1) == pytest.approx(10.7639, rel=1e-3)


def test_volume_liter_to_gallon():
    assert convert("volume", "liter", "gallon_us", 1) == pytest.approx(0.264172, rel=1e-4)


def test_speed_kmh_to_mph():
    assert convert("speed", "kilometers_per_hour", "miles_per_hour", 100) == pytest.approx(62.1371, rel=1e-3)


def test_time_hours_to_minutes():
    assert convert("time", "hour", "minute", 2) == 120


def test_temperature_celsius_to_fahrenheit():
    assert convert_temperature("celsius", "fahrenheit", 0) == pytest.approx(32)
    assert convert_temperature("celsius", "fahrenheit", 100) == pytest.approx(212)


def test_temperature_fahrenheit_to_celsius():
    assert convert_temperature("fahrenheit", "celsius", 32) == pytest.approx(0)


def test_temperature_celsius_to_kelvin():
    assert convert_temperature("celsius", "kelvin", 0) == pytest.approx(273.15)


def test_temperature_via_convert_dispatch():
    assert convert("temperature", "celsius", "fahrenheit", 0) == pytest.approx(32)


def test_data_storage_decimal_kilobyte_is_1000_bytes():
    assert convert("data_storage", "kilobyte", "byte", 1) == 1000


def test_data_storage_binary_kibibyte_is_1024_bytes():
    assert convert("data_storage", "kibibyte", "byte", 1) == 1024


def test_kb_and_kib_are_not_equal():
    kb_in_bytes = convert("data_storage", "kilobyte", "byte", 1)
    kib_in_bytes = convert("data_storage", "kibibyte", "byte", 1)
    assert kb_in_bytes != kib_in_bytes


def test_data_storage_gigabyte_to_megabyte():
    assert convert("data_storage", "gigabyte", "megabyte", 1) == 1000


def test_data_storage_gibibyte_to_mebibyte():
    assert convert("data_storage", "gibibyte", "mebibyte", 1) == 1024


def test_unknown_category_raises():
    with pytest.raises(ConversionError):
        convert("volume_of_sound", "meter", "foot", 1)


def test_unknown_unit_raises():
    with pytest.raises(ConversionError):
        convert("length", "meter", "smoots", 1)


def test_unknown_temperature_unit_raises():
    with pytest.raises(ConversionError):
        convert_temperature("celsius", "rankine", 0)


def test_round_trip_length():
    original = 42.0
    feet = convert("length", "meter", "foot", original)
    back = convert("length", "foot", "meter", feet)
    assert back == pytest.approx(original, rel=1e-9)
