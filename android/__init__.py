"""Android (Kivy) frontend for Cinqic Calculator.

This package is a separate, independent frontend that reuses the
platform-independent core in ``cinqic_calculator`` unchanged. It does not
import, depend on, or affect ``cinqic_calculator.ui`` (the Tkinter desktop
frontend) in any way.

Note on imports within this package: on an Android device, python-for-android
runs ``android/main.py`` with ``android/`` itself as the app root (buildozer's
``source.dir``), so sibling modules here (``logic``, ``android_constants``,
``screens``) import each other with flat, package-relative-free names (e.g.
``from logic import ...``) rather than ``from android.logic import ...``.
That also happens to work unmodified for local desktop development, since
Python puts a script's own directory first on ``sys.path`` when it is run
directly (``python android/main.py``). Only test code (``tests/test_android_glue.py``)
addresses modules here via the dotted ``android.<module>`` path, since it
runs from the repository root under pytest.
"""
