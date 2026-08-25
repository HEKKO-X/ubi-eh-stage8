#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Single unattended entry point: rebuilds clean, runs enumeration,
both path automations, remediation, and detection fixtures.
Reads foothold_user from candidate.json automatically - no manual input.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RANGE_SCRIPT = ROOT / "evidence" / "lab-source" / "portable_range.py"
CANDIDATE = ROOT / "candidate.json"
RANGE_ROOT = ROOT / "ad-range"


def run(cmd: list, label: str) -> bool:
    print(f"\n--- {label} ---")
    result = subprocess.run(cmd, cwd=ROOT)
    ok = result.returncode == 0
    print(f"--- {label}: {'PASS' if ok else 'FAIL'} ---")
    return ok


def main() -> None:
    with open(CANDIDATE) as f:
        foothold = json.load(f)["foothold_user"]

    results = {}

    results["build"] = run(
        [sys.executable, str(RANGE_SCRIPT), "build", "--assignment", str(CANDIDATE),
         "--out", str(RANGE_ROOT), "--force"],
        "Build clean range",
    )
    results["health"] = run(
        [sys.executable, str(RANGE_SCRIPT), "health", "--root", str(RANGE_ROOT)],
        "Health check",
    )
    results["enumeration"] = run(
        [sys.executable, str(ROOT / "enumeration" / "discover.py"),
         str(RANGE_ROOT / "source-records.json"), foothold],
        "Enumeration / discovery",
    )
    results["path1"] = run(
        [sys.executable, str(ROOT / "automation" / "path1_automation.py"),
         str(RANGE_SCRIPT), str(CANDIDATE), str(RANGE_ROOT)],
        "Path 1 automation (3x)",
    )
    results["path2"] = run(
        [sys.executable, str(ROOT / "automation" / "path2_automation.py"),
         str(RANGE_SCRIPT), str(CANDIDATE), str(RANGE_ROOT)],
        "Path 2 automation (3x)",
    )
    results["remediation"] = run(
        [sys.executable, str(ROOT / "remediation" / "remediation_test.py"),
         str(RANGE_SCRIPT), str(CANDIDATE), str(RANGE_ROOT)],
        "Remediation verification",
    )

    fixtures_dir = ROOT / "detections" / "fixtures"
    detection_ok = True
    for fixture in sorted(fixtures_dir.glob("*.jsonl")):
        ok = run(
            [sys.executable, str(ROOT / "detections" / "detect.py"), str(fixture)],
            f"Detection fixture: {fixture.name}",
        )
        detection_ok = detection_ok and ok
    results["detection_fixtures"] = detection_ok

    print("\n=== FINAL TEST SUMMARY ===")
    all_pass = True
    for name, ok in results.items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
        all_pass = all_pass and ok

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
