"""Application entry point: wires settings/history storage to the UI."""

import sys

from . import constants
from .history import History
from .settings import Settings

_USAGE = f"""{constants.APP_NAME} {constants.APP_VERSION}

Usage: cinqic-calculator [options]

Options:
  --version   Print the version and exit.
  --help      Show this message and exit.

Runs a windowed calculator when given no options. Works entirely offline.
"""


def run(argv=None):
    """Start the desktop application, or handle a command-line option.

    ``--version`` deliberately avoids importing the UI, so a packaged build
    can be smoke-tested on a machine (or CI runner) with no display at all.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--version" in argv or "-V" in argv:
        print(f"{constants.APP_NAME} {constants.APP_VERSION}")
        return 0
    if "--help" in argv or "-h" in argv:
        print(_USAGE)
        return 0

    from .ui.main_window import MainWindow

    data_dir = constants.data_dir()
    settings = Settings(Settings.default_path(data_dir))
    history = History(
        History.default_path(data_dir),
        max_entries=constants.MAX_HISTORY_ENTRIES,
        enabled=settings.get("save_history", True),
    )
    window = MainWindow(settings, history)
    window.mainloop()
    return 0
