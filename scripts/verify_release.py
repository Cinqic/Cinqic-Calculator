"""Verify that expected release artifacts exist and match SHA256SUMS.txt."""

import hashlib
import sys
from pathlib import Path

EXPECTED_FILES = [
    "Cinqic-Calculator-Windows-x64-Setup.exe",
    "Cinqic-Calculator-Windows-x64-Portable.zip",
    "SHA256SUMS.txt",
]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv):
    directory = Path(argv[0]) if argv else Path(".")
    errors = []

    for name in EXPECTED_FILES:
        if not (directory / name).is_file():
            errors.append(f"Missing release file: {name}")

    checksum_file = directory / "SHA256SUMS.txt"
    if checksum_file.is_file():
        expected = {}
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                errors.append(f"Malformed line in SHA256SUMS.txt: {line!r}")
                continue
            checksum, filename = parts
            expected[filename.strip()] = checksum.strip()

        for filename, expected_checksum in expected.items():
            file_path = directory / filename
            if not file_path.is_file():
                errors.append(f"SHA256SUMS.txt references missing file: {filename}")
                continue
            actual = sha256_of(file_path)
            if actual != expected_checksum:
                errors.append(f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("All expected release files present and checksums verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
