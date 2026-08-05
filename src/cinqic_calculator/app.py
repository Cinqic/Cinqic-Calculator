"""Application entry point: wires settings/history storage to the UI."""

from . import constants
from .history import History
from .settings import Settings
from .ui.main_window import MainWindow


def run():
    data_dir = constants.data_dir()
    settings = Settings(Settings.default_path(data_dir))
    history = History(
        History.default_path(data_dir),
        max_entries=constants.MAX_HISTORY_ENTRIES,
        enabled=settings.get("save_history", True),
    )
    window = MainWindow(settings, history)
    window.mainloop()
