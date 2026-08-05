import os

from cinqic_calculator.history import History


def test_add_entry(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path)
    history.add("2 + 2", "4", "2026-01-01T00:00:00")
    assert len(history.entries) == 1
    assert history.entries[0]["result"] == "4"


def test_history_persists_to_disk(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path)
    history.add("1 + 1", "2", "2026-01-01T00:00:00")

    reloaded = History(path)
    assert len(reloaded.entries) == 1
    assert reloaded.entries[0]["expression"] == "1 + 1"


def test_max_entries_enforced(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path, max_entries=5)
    for i in range(10):
        history.add(str(i), str(i), "2026-01-01T00:00:00")
    assert len(history.entries) == 5
    assert history.entries[-1]["expression"] == "9"


def test_delete_entry(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path)
    history.add("1", "1", "t")
    history.add("2", "2", "t")
    history.delete_at(0)
    assert len(history.entries) == 1
    assert history.entries[0]["expression"] == "2"


def test_clear_history(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path)
    history.add("1", "1", "t")
    history.clear()
    assert history.entries == []


def test_disabled_history_does_not_write(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    history = History(path, enabled=False)
    history.add("1", "1", "t")
    assert not os.path.exists(path)
    assert history.entries == []


def test_recovers_from_malformed_file(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{not valid json[[[")
    history = History(path)
    assert history.entries == []


def test_recovers_from_wrong_type_file(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('{"not": "a list"}')
    history = History(path)
    assert history.entries == []


def test_ignores_malformed_entries(tmp_path):
    path = os.path.join(tmp_path, "history.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write('[{"expression": "1+1"}, {"expression": "2+2", "result": "4", "timestamp": "t"}]')
    history = History(path)
    assert len(history.entries) == 1
    assert history.entries[0]["expression"] == "2+2"
