"""Inspect a built Android APK's package identity, versions, SDK levels, and
requested permissions using the Android SDK's `aapt` (or `aapt2`) tool.

Run in CI (Linux, Android SDK build-tools on PATH or under $ANDROID_HOME)
after a debug or release APK is built, before it's ever installed, signed,
or published. Exits non-zero if the APK doesn't match expectations -- most
importantly, if it requests ANY permission beyond the explicit allowlist
(empty by default: this app is offline-only and needs no permissions).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_PACKAGE = "com.cinqic.calculator"

# Deliberately empty: the app is fully offline, uses only its private Kivy
# user_data_dir, and needs no permission for that. Any permission found in
# the APK that isn't in this set fails the build.
ALLOWED_PERMISSIONS: set[str] = set()


def find_aapt() -> str:
    for name in ("aapt2", "aapt"):
        path = shutil.which(name)
        if path:
            return path

    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        build_tools_dir = Path(android_home) / "build-tools"
        if build_tools_dir.is_dir():
            versions = sorted(build_tools_dir.iterdir(), reverse=True)
            for version_dir in versions:
                for name in ("aapt2", "aapt"):
                    candidate = version_dir / name
                    if candidate.is_file():
                        return str(candidate)

    raise SystemExit("Could not find aapt or aapt2 on PATH or under $ANDROID_HOME/build-tools/*")


def dump_badging(aapt: str, apk_path: Path) -> str:
    is_aapt2 = Path(aapt).name.startswith("aapt2")
    cmd = [aapt, "dump", "badging", str(apk_path)] if not is_aapt2 else [aapt, "dump", "badging", str(apk_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"aapt dump badging failed:\n{result.stderr}")
    return result.stdout


def parse_badging(output: str) -> dict:
    info = {"permissions": []}

    package_match = re.search(
        r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", output
    )
    if package_match:
        info["package"] = package_match.group(1)
        info["version_code"] = package_match.group(2)
        info["version_name"] = package_match.group(3)

    min_sdk_match = re.search(r"sdkVersion:'(\d+)'", output)
    if min_sdk_match:
        info["min_sdk"] = int(min_sdk_match.group(1))

    target_sdk_match = re.search(r"targetSdkVersion:'(\d+)'", output)
    if target_sdk_match:
        info["target_sdk"] = int(target_sdk_match.group(1))

    for perm_match in re.finditer(r"uses-permission[^:]*: name='([^']+)'", output):
        info["permissions"].append(perm_match.group(1))

    launchable = re.search(r"launchable-activity: name='([^']+)'", output)
    if launchable:
        info["launchable_activity"] = launchable.group(1)

    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk_path", type=Path)
    parser.add_argument(
        "--allow-permission",
        action="append",
        default=[],
        help="Permit an additional permission beyond ALLOWED_PERMISSIONS (repeatable).",
    )
    args = parser.parse_args()

    if not args.apk_path.is_file():
        raise SystemExit(f"APK not found: {args.apk_path}")

    aapt = find_aapt()
    badging = dump_badging(aapt, args.apk_path)
    info = parse_badging(badging)

    problems = []

    if info.get("package") != EXPECTED_PACKAGE:
        problems.append(f"package name is {info.get('package')!r}, expected {EXPECTED_PACKAGE!r}")

    allowed = ALLOWED_PERMISSIONS | set(args.allow_permission)
    unexpected = [p for p in info["permissions"] if p not in allowed]
    if unexpected:
        problems.append(f"unexpected permission(s) requested: {unexpected}")

    if not info.get("launchable_activity"):
        problems.append("no launchable activity found (app would not appear in the launcher)")

    print("APK inspection:")
    print(f"  file            : {args.apk_path}")
    print(f"  package         : {info.get('package')}")
    print(f"  versionName     : {info.get('version_name')}")
    print(f"  versionCode     : {info.get('version_code')}")
    print(f"  minSdkVersion   : {info.get('min_sdk')}")
    print(f"  targetSdkVersion: {info.get('target_sdk')}")
    print(f"  permissions     : {info['permissions'] or '(none)'}")
    print(f"  launchable      : {info.get('launchable_activity')}")

    if problems:
        print("\nFAIL:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nPASS: package identity, permissions, and launchability all as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
