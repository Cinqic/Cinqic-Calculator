"""Local, persistent user settings. Never transmitted anywhere."""

import os

from . import storage

__all__ = ["Settings", "DEFAULT_SETTINGS"]

DEFAULT_SETTINGS = {
    "theme": "dark",
    "save_history": True,
    "degree_mode": True,
    "persist_memory": False,
    "memory_value": None,
    "window_width": 900,
    "window_height": 720,
    "window_x": None,
    "window_y": None,
}


class Settings:
    """Loads, validates, and persists settings as a plain dict on disk."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.values = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        loaded = storage.read_json(self.file_path, {})
        if not isinstance(loaded, dict):
            loaded = {}
        merged = dict(DEFAULT_SETTINGS)
        for key, default_value in DEFAULT_SETTINGS.items():
            if key not in loaded:
                continue
            value = loaded[key]
            if default_value is None or isinstance(value, type(default_value)):
                merged[key] = value
        self.values = merged

    def save(self) -> None:
        storage.write_json(self.file_path, self.values)

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value) -> None:
        self.values[key] = value

    @classmethod
    def default_path(cls, data_dir: str) -> str:
        return os.path.join(data_dir, "settings.json")
