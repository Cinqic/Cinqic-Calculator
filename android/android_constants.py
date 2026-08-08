"""Android-app-only constants.

Deliberately kept separate from ``cinqic_calculator.constants``: that module
is shared with the Tkinter desktop frontend and its ``APP_VERSION``
("1.0.1" as of this writing) tracks the *desktop Windows* release. The
Android app is packaged and versioned independently (its own
``buildozer.spec`` ``version``/``android.numeric_version``), so it gets its
own small constants module instead of overloading the shared one.
"""

ANDROID_APP_VERSION = "1.0.0"
ANDROID_VERSION_CODE = 1

PRIVACY_SUMMARY = (
    "Cinqic Calculator works fully offline. There is no account, no ads, "
    "no analytics, and no telemetry. Calculations, history, and settings "
    "are stored only in this app's private storage on your device and are "
    "never transmitted anywhere. The app requests no Android permissions, "
    "including no internet permission."
)

JUNIPER_RELATIONSHIP_TEXT = (
    "Juniper is not integrated into Cinqic Calculator. The calculator "
    "works fully without AI. Juniper is Cinqic's future local-first "
    "assistant."
)
