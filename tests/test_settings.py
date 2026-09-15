import json
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


# ---------------------------------------------------------------------------
# Upgrading from an earlier version's settings file
# ---------------------------------------------------------------------------
def test_settings_file_from_1_0_1_gains_the_new_defaults(tmp_path):
    """An existing install must keep its choices and pick up new keys."""
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "theme": "light",
                "save_history": False,
                "degree_mode": False,
                "persist_memory": True,
                "memory_value": 12.5,
                "window_width": 900,
                "window_height": 600,
            }
        ),
        encoding="utf-8",
    )

    settings = Settings(str(path))

    # Existing preferences survive.
    assert settings.get("theme") == "light"
    assert settings.get("save_history") is False
    assert settings.get("degree_mode") is False
    assert settings.get("persist_memory") is True
    assert settings.get("memory_value") == 12.5

    # New 1.1.0 keys arrive at their defaults: animations on, haptics on.
    assert settings.get("reduced_motion") is False
    assert settings.get("haptics") is True


def test_unknown_keys_from_a_future_version_are_dropped_safely(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "dark", "some_future_option": {"nested": True}}), encoding="utf-8")
    settings = Settings(str(path))
    assert settings.get("theme") == "dark"
    assert settings.get("some_future_option") is None


def test_a_corrupt_settings_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json at all", encoding="utf-8")
    settings = Settings(str(path))
    assert settings.get("theme") == "dark"
    assert settings.get("haptics") is True


def test_wrongly_typed_values_are_rejected_in_favour_of_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"reduced_motion": "yes please", "save_history": 7}), encoding="utf-8")
    settings = Settings(str(path))
    assert settings.get("reduced_motion") is False
    assert settings.get("save_history") is True
