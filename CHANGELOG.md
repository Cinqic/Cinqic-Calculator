# Changelog

All notable changes to Cinqic Calculator are documented in this file.
Windows and Android are versioned and released independently (Windows tags:
`vX.Y.Z`; Android tags: `android-vX.Y.Z`).

## Android 1.0.0

### Added

- A separate, independent Android frontend built with Kivy, reusing the
  same tested calculator, evaluator, financial, conversion, history,
  settings, and storage logic as the Windows app unchanged.
- Standard and scientific calculator, memory (MC/MR/M+/M-/MS) with the
  same enabled/disabled and cross-view isolation behavior as the desktop
  v1.0.1 fixes, unit conversions, financial tools, local history, settings,
  and About/privacy screens.
- Fully offline. No internet permission, no unnecessary permissions.
- Package `com.cinqic.calculator`, distributed as a direct signed APK
  download with a published SHA-256 checksum and signing certificate
  fingerprint — not through the Google Play Store.

## 1.0.1

### Fixed

- `MC` and `MR` are now disabled whenever memory is empty, instead of
  always appearing clickable regardless of state.
- Keyboard shortcuts (digits, operators, Enter, Escape, Backspace) no
  longer leak into the calculator's hidden state while another view
  (Convert, Financial, History, Settings, About) is active. Previously,
  typing into an entry field on another view also silently drove the
  invisible calculator's state, which could later surface as unexpected
  values or memory behavior when returning to the Calculator view.
- The "Remember calculator memory between sessions" setting now actually
  works: memory is restored on startup when enabled, saved whenever it
  changes, and cleared from disk immediately when the setting is turned
  off. Previously the checkbox had no effect at all, and even a direct
  write to this setting would have been silently dropped on reload.

### Improved

- The memory indicator and `MC`/`MR` state are now initialized correctly
  as soon as the calculator view is built, rather than only updating
  after the first button press.

## 1.0.0

Initial release.

### Added

- Standard calculator: addition, subtraction, multiplication, division,
  decimals, positive/negative values, percentage, square root, clear entry,
  clear all, backspace, and repeated-equals behavior.
- Collapsible scientific mode: square, cube, arbitrary exponent (via
  keyboard expression entry), square root, cube root, reciprocal,
  factorial, absolute value, pi, e, natural log, base-10 log, sine, cosine,
  tangent, and a degree/radian toggle.
- Calculator memory: MC, MR, M+, M-, MS with a visible memory indicator.
- Keyboard shortcuts for digits, operators, equals, clear, backspace, copy,
  paste, clear history, settings, and help.
- Unit conversion for length, mass, temperature, area, volume, speed, time,
  and data storage — with decimal (KB, MB, GB) and binary (KiB, MiB, GiB)
  data units kept explicitly distinct.
- Financial tools: percentage of/increase/decrease/difference, discount,
  sales tax, final price, tip, bill splitting, simple interest, and
  compound interest, using `Decimal` internally for currency accuracy.
- Local calculation history (up to 200 entries) with copy, reuse, delete,
  and clear-all, and a setting to disable history saving entirely.
- Local settings with dark, light, and system themes.
- A Windows installer and a portable ZIP build, both produced via
  PyInstaller and GitHub Actions.

### Known limitations

- Windows only (10/11, 64-bit) for this release.
- The build is not code-signed; Windows SmartScreen may show an
  unfamiliar-app warning on first run.
- Juniper is not integrated into this release. The calculator works fully
  without AI.
