# Privacy

Cinqic Calculator is designed to work entirely on your device.

## What the application does

- Does **not** require an account.
- Does **not** include advertising.
- Does **not** include analytics.
- Does **not** include telemetry.
- Does **not** transmit your calculations, history, or settings anywhere.
- Stores settings and (optionally) calculation history locally, in
  `%LOCALAPPDATA%\Cinqic\Calculator\` on Windows.
- Works fully offline. An internet connection is never required to use it.
- Does **not** currently include Juniper or any other AI model. Juniper is
  not integrated into Cinqic Calculator 1.0.

## Local data

Two small JSON files may exist in the application data directory:

- `settings.json` — your theme, degree/radian mode, and history preference.
- `history.json` — recent calculations, if history saving is enabled.

Both files are written atomically and are readable/editable by you. Neither
is ever read by, or sent to, any server. Disabling "Save calculation
history" in Settings stops new history from being written; existing history
can be deleted from the History or Settings view at any time.

## Dependencies

Cinqic Calculator has no third-party runtime dependencies — the interface
uses only Python's standard library (`tkinter`). The dependency tree was
kept intentionally minimal so there is nothing bundled that could make
unexpected network or analytics calls.

## Crash reporting

No crash-reporting or error-telemetry service is included.

## Questions

Cinqic Calculator is open source. You can read the exact source code that
implements everything described here in this repository.
