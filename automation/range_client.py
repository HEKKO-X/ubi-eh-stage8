#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Shared client for talking to portable_range.py's `act` command.
Both path automations import this instead of duplicating subprocess logic.
"""
import json
import subprocess
import sys
from pathlib import Path


def run_operation(range_script: Path, assignment: Path, root: Path, operation: str) -> dict:
    """
    Runs one `act` operation against the range and returns the parsed
    JSON result, plus the raw exit code. Never raises on a 'denied'
    result - that's a valid outcome we need to detect, not a crash.
    """
    proc = subprocess.run(
        [
            sys.executable, str(range_script), "act",
            "--assignment", str(assignment),
            "--root", str(root),
            operation,
        ],
        capture_output=True,
        text=True,
    )
    try:
        parsed = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        parsed = {"operation": operation, "ok": False, "raw_stdout": proc.stdout, "raw_stderr": proc.stderr}

    parsed["exit_code"] = proc.returncode
    return parsed


def rebuild_range(range_script: Path, assignment: Path, out: Path) -> dict:
    """
    Resets the range to a clean checkpoint by rebuilding it from scratch.
    This IS our 'clean checkpoint' - portable_range.py has no separate
    snapshot/restore command, so a fresh --force build is the reset.
    """
    proc = subprocess.run(
        [
            sys.executable, str(range_script), "build",
            "--assignment", str(assignment),
            "--out", str(out),
            "--force",
        ],
        capture_output=True,
        text=True,
    )
    try:
        parsed = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        parsed = {"status": "error", "raw_stdout": proc.stdout, "raw_stderr": proc.stderr}
    parsed["exit_code"] = proc.returncode
    return parsed


def run_sequence(range_script: Path, assignment: Path, root: Path, operations: list) -> list:
    """
    Runs a list of operations in order. Stops early if one fails,
    since later steps depend on earlier ones succeeding (e.g.
    request-service-token needs set-spn to have run first).
    """
    results = []
    for op in operations:
        result = run_operation(range_script, assignment, root, op)
        results.append(result)
        if not result.get("ok", False):
            break
    return results


def load_assignment_raw(assignment: Path) -> dict:
    """Reads the candidate JSON directly - used only to VERIFY a
    returned proof matches, never to hardcode the value anywhere."""
    with open(assignment, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_proof(results: list, assignment: Path, proof_field: str) -> bool:
    """
    Confirms the last successful result's 'proof' value matches the
    real value in the candidate JSON, read fresh at verification time.
    """
    a = load_assignment_raw(assignment)
    expected = a.get(proof_field)
    for r in results:
        if r.get("ok") and r.get("proof") == expected:
            return True
    return False


def check_health(range_script: Path, root: Path) -> dict:
    """
    Runs the range's own health command and returns the parsed result.
    Used to confirm the range is still green AFTER remediation is applied.
    """
    proc = subprocess.run(
        [sys.executable, str(range_script), "health", "--root", str(root)],
        capture_output=True,
        text=True,
    )
    try:
        parsed = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        parsed = {"healthy": False, "raw_stdout": proc.stdout, "raw_stderr": proc.stderr}
    parsed["exit_code"] = proc.returncode
    return parsed
