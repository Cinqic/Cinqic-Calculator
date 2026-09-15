#!/usr/bin/env bash
#
# Builds Cinqic Calculator for Linux (x86_64): runs the test suite, packages
# with PyInstaller, produces a standalone tarball, and generates checksums.
# Exits non-zero on failure.
#
# Requires a Python with tkinter available (python3-tk on Debian/Ubuntu,
# python3-tkinter on Fedora) -- PyInstaller can only bundle Tk if the
# interpreter building the app can import it.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV_PATH="${BUILD_VENV:-$REPO_ROOT/.build-venv-linux}"
DIST_PATH="$REPO_ROOT/dist"
BUILD_PATH="$REPO_ROOT/build"
OUTPUT_PATH="$REPO_ROOT/dist/linux"
APP_NAME="CinqicCalculator"
TARBALL="Cinqic-Calculator-Linux-x86_64.tar.gz"

echo "== 1. Create/refresh virtual environment =="
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi
PYTHON="$VENV_PATH/bin/python"

echo "== 2. Confirm tkinter is importable =="
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
    echo "ERROR: tkinter is not available to $PYTHON." >&2
    echo "Install your distribution's Tk package (e.g. 'sudo apt install python3-tk')" >&2
    echo "and recreate the build virtual environment." >&2
    exit 1
fi

echo "== 3. Install pinned build dependencies =="
"$PYTHON" -m pip install --upgrade pip -q
"$PYTHON" -m pip install -e "$REPO_ROOT" -q
"$PYTHON" -m pip install -r "$REPO_ROOT/requirements-build.txt" -q

echo "== 4. Run tests =="
"$PYTHON" -m pytest "$REPO_ROOT/tests" -q

echo "== 5. Remove previous build output =="
rm -rf "$DIST_PATH" "$BUILD_PATH" "$OUTPUT_PATH"

echo "== 6. Build application with PyInstaller =="
"$PYTHON" -m PyInstaller \
    --name "$APP_NAME" \
    --windowed \
    --onedir \
    --noconfirm \
    --paths "$REPO_ROOT/src" \
    "$REPO_ROOT/src/cinqic_calculator/__main__.py"

APP_DIR="$DIST_PATH/$APP_NAME"
if [ ! -x "$APP_DIR/$APP_NAME" ]; then
    echo "ERROR: expected PyInstaller output not found: $APP_DIR/$APP_NAME" >&2
    exit 1
fi

echo "== 7. Add a launcher and desktop entry =="
# The binary lives in the bundle directory next to its libraries; this wrapper
# lets the tarball be extracted anywhere and run without cd-ing into it first.
cat > "$APP_DIR/cinqic-calculator" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec "$HERE/CinqicCalculator" "$@"
LAUNCHER
chmod +x "$APP_DIR/cinqic-calculator"

cp "$REPO_ROOT/assets/icons/cinqic-calculator.png" "$APP_DIR/cinqic-calculator.png"
cat > "$APP_DIR/cinqic-calculator.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Cinqic Calculator
Comment=A private, offline calculator
Exec=cinqic-calculator
Icon=cinqic-calculator
Categories=Utility;Calculator;
Terminal=false
DESKTOP

cp "$REPO_ROOT/LICENSE" "$APP_DIR/LICENSE"
if [ -f "$REPO_ROOT/NOTICE" ]; then
    cp "$REPO_ROOT/NOTICE" "$APP_DIR/NOTICE"
fi

echo "== 8. Smoke-test the packaged binary =="
"$APP_DIR/cinqic-calculator" --version

echo "== 9. Build the tarball =="
mkdir -p "$OUTPUT_PATH"
tar -czf "$OUTPUT_PATH/$TARBALL" -C "$DIST_PATH" "$APP_NAME"

echo "== 10. Generate SHA-256 checksums =="
"$PYTHON" "$REPO_ROOT/scripts/calculate_checksum.py" \
    "$OUTPUT_PATH/SHA256SUMS-Linux.txt" \
    "$OUTPUT_PATH/$TARBALL"

echo "== 11. Verify expected artifacts exist =="
"$PYTHON" "$REPO_ROOT/scripts/verify_release.py" "$OUTPUT_PATH" linux

echo "Build complete. Artifacts in $OUTPUT_PATH"
