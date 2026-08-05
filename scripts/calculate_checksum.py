"""Generate SHA256SUMS.txt for one or more release files."""

import hashlib
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv):
    if len(argv) < 2:
        print("Usage: calculate_checksum.py <output_file.txt> <file1> [file2 ...]", file=sys.stderr)
        return 1

    output_path = Path(argv[0])
    file_paths = [Path(p) for p in argv[1:]]

    missing = [p for p in file_paths if not p.is_file()]
    if missing:
        for p in missing:
            print(f"Missing expected release file: {p}", file=sys.stderr)
        return 1

    lines = []
    for path in file_paths:
        checksum = sha256_of(path)
        lines.append(f"{checksum}  {path.name}")
        print(f"{checksum}  {path.name}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
