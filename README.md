# Cinqic Calculator

A lightweight, private desktop calculator for Windows.

![Cinqic Calculator screenshot](assets/screenshots/calculator.png)

Perform standard and scientific calculations, convert common units, review
local calculation history, and use practical financial tools — without an
account, cloud service, or internet connection.

**Juniper is not integrated into Cinqic Calculator 1.0. The calculator
works locally without AI.** Juniper is Cinqic's future local-first
assistant; this app is built with it in mind, honestly, without pretending
it's already here. See [About Juniper](#juniper-relationship) below.

## Features

- Standard calculator: arithmetic, decimals, percentages, square root,
  parentheses (via keyboard/scientific expression entry), backspace,
  clear entry/all, repeated equals.
- Collapsible scientific mode: powers, roots, reciprocal, factorial,
  absolute value, π, e, ln, log₁₀, sin/cos/tan with degree/radian toggle.
- Calculator memory (MC/MR/M+/M-/MS) with a visible indicator.
- Full keyboard shortcut support.
- Unit conversion: length, mass, temperature, area, volume, speed, time,
  and data storage (decimal KB/MB/GB kept distinct from binary KiB/MiB/GiB).
- Financial tools: percentages, discounts, sales tax, tips, bill splitting,
  simple and compound interest — clearly labeled as estimates.
- Local calculation history (up to 200 entries), fully optional.
- Dark, light, and system themes.
- Fully offline. No account, no telemetry, no ads.

## Windows system requirements

- Windows 10 or Windows 11, 64-bit.
- No other software required — the installer and portable build include
  everything needed to run.

## Installation

1. Download `Cinqic-Calculator-Windows-x64-Setup.exe` from the
   [latest release](https://github.com/Cinqic/Cinqic-Calculator/releases/latest).
2. Run the installer and follow the prompts. Administrator privileges are
   not required after installation.
3. Launch **Cinqic Calculator** from the Start menu.

A portable version (`Cinqic-Calculator-Windows-x64-Portable.zip`) is also
available if you'd rather not install anything — unzip it and run
`CinqicCalculator.exe` directly.

**SmartScreen note:** this build is not code-signed. Windows may show an
"unrecognized app" warning the first time you run it. This is expected for
an unsigned open-source app; you can review the source code yourself before
choosing to continue.

Verify your download against `SHA256SUMS.txt` from the same release if
you'd like to confirm file integrity.

## Development setup

```powershell
git clone https://github.com/Cinqic/Cinqic-Calculator.git
cd Cinqic-Calculator
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install -r requirements-build.txt
```

Run the app from source:

```powershell
python -m cinqic_calculator
```

## Tests

```powershell
python -m pytest tests/ -v
```

## Build (Windows)

```powershell
powershell -File scripts/build_windows.ps1
```

This creates a virtual environment, runs the test suite, builds the
PyInstaller application, builds the Inno Setup installer and portable ZIP,
and generates `SHA256SUMS.txt`. It exits non-zero if any step fails.

## Privacy

Cinqic Calculator stores settings and optional history locally in
`%LOCALAPPDATA%\Cinqic\Calculator\` and never transmits them anywhere. See
[PRIVACY.md](PRIVACY.md) for details.

## Juniper relationship

Cinqic Calculator is Cinqic's first small public software product. It is
useful entirely on its own, without AI. Juniper — Cinqic's lightweight,
local-first assistant — is still in development and is **not** integrated
into this release. Future versions may add optional local Juniper
explanations, while the calculator keeps working fully without them.

> AI should remain a choice.

## Release process

Tagging a commit `vX.Y.Z` on `main` triggers
[`release-windows.yml`](.github/workflows/release-windows.yml), which runs
the test suite, builds the installer and portable ZIP, generates checksums,
and publishes a GitHub Release with those assets attached. Releases are
only published when tests and packaging succeed.

## License

MIT — see [LICENSE](LICENSE).
