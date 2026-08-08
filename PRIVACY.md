# Privacy

Cinqic Calculator is designed to work entirely on your device.

## What the application does

- Does **not** require an account.
- Does **not** include advertising.
- Does **not** include analytics.
- Does **not** include telemetry.
- Does **not** transmit your calculations, history, or settings anywhere.
- Stores settings and (optionally) calculation history locally — in
  `%LOCALAPPDATA%\Cinqic\Calculator\` on Windows, or the app's private
  Android storage (`Context.getFilesDir()`-equivalent, via Kivy's
  `user_data_dir`) on Android.
- Works fully offline. An internet connection is never required to use it.
  The Android app requests no internet permission at all.
- Does **not** currently include Juniper or any other AI model. Juniper is
  not integrated into Cinqic Calculator on either platform.

## Local data

Two small JSON files may exist in the application's private data directory
on either platform:

- `settings.json` — your theme, degree/radian mode, and history preference.
- `history.json` — recent calculations, if history saving is enabled.

Both files are written atomically and are readable/editable by you. Neither
is ever read by, or sent to, any server. Disabling "Save calculation
history" in Settings stops new history from being written; existing history
can be deleted from the History or Settings view at any time.

On Android, this data lives in the app's private storage, which no other
app can read, and which is deleted automatically when the app is
uninstalled — there is nothing left behind to clean up manually.

## Permissions (Android)

The Android app requests no permissions: no internet, no storage access
beyond its own private app directory, and nothing else. You can confirm
this yourself in [`android/buildozer.spec`](android/buildozer.spec)
(`android.permissions =`, left empty) or by inspecting the APK's manifest.

## Dependencies

The core calculation, conversion, financial, history, and settings logic
(`src/cinqic_calculator/`) has no third-party runtime dependencies — pure
Python standard library. The Windows interface uses only `tkinter`, also
standard library. The Android interface additionally uses
[Kivy](https://kivy.org), an open-source UI toolkit, to draw the touch
interface; Kivy does not add any network, analytics, or telemetry
behavior on its own, and none is added by this app either.

## Crash reporting

No crash-reporting or error-telemetry service is included.

## Questions

Cinqic Calculator is open source. You can read the exact source code that
implements everything described here in this repository.
