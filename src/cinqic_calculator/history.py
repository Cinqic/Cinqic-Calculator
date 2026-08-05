"""Local calculation history. Never transmitted; capped to a fixed size."""

import os

from . import storage

__all__ = ["History", "DEFAULT_MAX_ENTRIES"]

DEFAULT_MAX_ENTRIES = 200


class History:
    """A bounded, disk-backed list of {expression, result, timestamp} entries."""

    def __init__(self, file_path: str, max_entries: int = DEFAULT_MAX_ENTRIES, enabled: bool = True):
        self.file_path = file_path
        self.max_entries = max_entries
        self.enabled = enabled
        self.entries = []
        self.load()

    def load(self) -> None:
        loaded = storage.read_json(self.file_path, [])
        if not isinstance(loaded, list):
            loaded = []
        cleaned = []
        for entry in loaded:
            if (
                isinstance(entry, dict)
                and "expression" in entry
                and "result" in entry
                and "timestamp" in entry
            ):
                cleaned.append(
                    {
                        "expression": str(entry["expression"]),
                        "result": str(entry["result"]),
                        "timestamp": str(entry["timestamp"]),
                    }
                )
        self.entries = cleaned[-self.max_entries :]

    def save(self) -> None:
        if self.enabled:
            storage.write_json(self.file_path, self.entries)

    def add(self, expression: str, result: str, timestamp: str) -> None:
        if not self.enabled:
            return
        self.entries.append({"expression": expression, "result": result, "timestamp": timestamp})
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
        self.save()

    def delete_at(self, index: int) -> None:
        if 0 <= index < len(self.entries):
            del self.entries[index]
            self.save()

    def clear(self) -> None:
        self.entries = []
        self.save()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            return

    @classmethod
    def default_path(cls, data_dir: str) -> str:
        return os.path.join(data_dir, "history.json")
