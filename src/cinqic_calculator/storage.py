"""Atomic, fault-tolerant local JSON file storage."""

import json
import os
import tempfile

__all__ = ["read_json", "write_json"]


def read_json(path: str, default):
    """Read JSON from ``path``. Returns ``default`` if the file is missing,
    empty, or malformed rather than raising — settings/history must degrade
    gracefully, never crash the app.
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        if not content.strip():
            return default
        return json.loads(content)
    except (OSError, ValueError):
        return default


def write_json(path: str, data) -> None:
    """Write ``data`` as JSON to ``path`` atomically (write-temp then replace)."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(temp_path, path)
    except OSError:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
