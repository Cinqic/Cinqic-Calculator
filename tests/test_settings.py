import os

from cinqic_calculator.settings import DEFAULT_SETTINGS, Settings


def test_defaults_when_no_file(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    settings = Settings(path)
    assert settings.get("theme") == DEFAULT_SETTINGS["theme"]
    assert settings.get("save_history") is True


def test_save_and_reload(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    settings = Settings(path)
    settings.set("theme", "light")
    settings.set("save_history", False)
    settings.save()

    reloaded = Settings(path)
    assert reloaded.get("theme") == "light"
    assert reloaded.get("save_history") is False


def test_recovers_from_malformed_file(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("not json at all {{{")
    settings = Settings(path)
    assert settings.get("theme") == DEFAULT_SETTINGS["theme"]


def test_recovers_from_wrong_type_file(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("[1, 2, 3]")
    settings = Settings(path)
    assert settings.get("theme") == DEFAULT_SETTINGS["theme"]


def test_ignores_unknown_and_wrong_type_keys(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('{"theme": 123, "unexpected_key": "x", "save_history": false}')
    settings = Settings(path)
    assert settings.get("theme") == DEFAULT_SETTINGS["theme"]
    assert settings.get("save_history") is False


def test_window_position_allows_none(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    settings = Settings(path)
    settings.set("window_x", 100)
    settings.save()
    reloaded = Settings(path)
    assert reloaded.get("window_x") == 100


def test_memory_value_defaults_to_none(tmp_path):
    path = os.path.join(tmp_path, "settings.json")
    settings = Settings(path)
    assert settings.get("memory_value") is None


def test_memory_value_round_trips(tmp_path):
    """Regression: memory_value must be in DEFAULT_SETTINGS, or load()
    silently drops it on reload since it only keeps known default keys."""
    path = os.path.join(tmp_path, "settings.json")
    settings = Settings(path)
    settings.set("memory_value", 42.0)
    settings.save()

    reloaded = Settings(path)
    assert reloaded.get("memory_value") == 42.0
