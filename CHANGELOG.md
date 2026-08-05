# Changelog

All notable changes to Cinqic Calculator are documented in this file.

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
