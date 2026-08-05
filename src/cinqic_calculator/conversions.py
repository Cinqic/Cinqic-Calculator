"""Deterministic unit conversion tables.

Data-storage units are explicit about decimal (SI, base-1000: KB, MB...) vs
binary (IEC, base-1024: KiB, MiB...) — they are never treated as equivalent.
"""

__all__ = ["CATEGORIES", "convert", "ConversionError"]


class ConversionError(ValueError):
    """Raised for unknown categories or units."""


# Length: base unit = meter
_LENGTH = {
    "millimeter": 0.001,
    "centimeter": 0.01,
    "meter": 1.0,
    "kilometer": 1000.0,
    "inch": 0.0254,
    "foot": 0.3048,
    "yard": 0.9144,
    "mile": 1609.344,
}

# Mass: base unit = gram
_MASS = {
    "milligram": 0.001,
    "gram": 1.0,
    "kilogram": 1000.0,
    "ounce": 28.349523125,
    "pound": 453.59237,
}

# Area: base unit = square meter
_AREA = {
    "square_meter": 1.0,
    "square_kilometer": 1_000_000.0,
    "square_foot": 0.09290304,
    "acre": 4046.8564224,
    "hectare": 10_000.0,
}

# Volume: base unit = liter
_VOLUME = {
    "milliliter": 0.001,
    "liter": 1.0,
    "cubic_meter": 1000.0,
    "gallon_us": 3.785411784,
    "quart_us": 0.946352946,
    "cup_us": 0.2365882365,
}

# Speed: base unit = meters per second
_SPEED = {
    "meters_per_second": 1.0,
    "kilometers_per_hour": 1000.0 / 3600.0,
    "miles_per_hour": 1609.344 / 3600.0,
}

# Time: base unit = second
_TIME = {
    "second": 1.0,
    "minute": 60.0,
    "hour": 3600.0,
    "day": 86400.0,
    "week": 604800.0,
}

# Data storage: base unit = byte. Decimal (base-1000, SI) and binary
# (base-1024, IEC) units are kept as distinct, separately named units.
_DATA_STORAGE = {
    "byte": 1.0,
    "kilobyte": 1_000.0,
    "megabyte": 1_000_000.0,
    "gigabyte": 1_000_000_000.0,
    "terabyte": 1_000_000_000_000.0,
    "kibibyte": 1024.0,
    "mebibyte": 1024.0**2,
    "gibibyte": 1024.0**3,
    "tebibyte": 1024.0**4,
}

CATEGORIES = {
    "length": _LENGTH,
    "mass": _MASS,
    "area": _AREA,
    "volume": _VOLUME,
    "speed": _SPEED,
    "time": _TIME,
    "data_storage": _DATA_STORAGE,
}


def convert(category: str, from_unit: str, to_unit: str, value: float) -> float:
    """Convert ``value`` from ``from_unit`` to ``to_unit`` within ``category``.

    Temperature is handled separately via convert_temperature() because it is
    not a simple linear scale factor.
    """
    if category == "temperature":
        return convert_temperature(from_unit, to_unit, value)

    table = CATEGORIES.get(category)
    if table is None:
        raise ConversionError(f"Unknown category: {category}")
    if from_unit not in table:
        raise ConversionError(f"Unknown unit '{from_unit}' in category '{category}'")
    if to_unit not in table:
        raise ConversionError(f"Unknown unit '{to_unit}' in category '{category}'")

    base_value = value * table[from_unit]
    return base_value / table[to_unit]


_TEMPERATURE_UNITS = {"celsius", "fahrenheit", "kelvin"}


def convert_temperature(from_unit: str, to_unit: str, value: float) -> float:
    if from_unit not in _TEMPERATURE_UNITS:
        raise ConversionError(f"Unknown temperature unit: {from_unit}")
    if to_unit not in _TEMPERATURE_UNITS:
        raise ConversionError(f"Unknown temperature unit: {to_unit}")

    celsius = _to_celsius(from_unit, value)
    return _from_celsius(to_unit, celsius)


def _to_celsius(unit: str, value: float) -> float:
    if unit == "celsius":
        return value
    if unit == "fahrenheit":
        return (value - 32) * 5.0 / 9.0
    if unit == "kelvin":
        return value - 273.15
    raise ConversionError(f"Unknown temperature unit: {unit}")


def _from_celsius(unit: str, celsius: float) -> float:
    if unit == "celsius":
        return celsius
    if unit == "fahrenheit":
        return celsius * 9.0 / 5.0 + 32
    if unit == "kelvin":
        return celsius + 273.15
    raise ConversionError(f"Unknown temperature unit: {unit}")
