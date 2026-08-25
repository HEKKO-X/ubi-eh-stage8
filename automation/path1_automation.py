#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Path 1 automation: WriteSPN -> Kerberoast-style credential abuse -> ReadProof.
Sequence: set-spn -> request-service-token -> read-proof-1 -> cleanup
Runs 3 times from a clean checkpoint, verifies the real proof each time,
and always cleans up temporary artifacts afterward - even on failure.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from range_client import rebuild_range, run_sequence, verify_proof, run_operation

PATH1_SEQUENCE = ["set-spn", "request-service-token", "read-proof-1"]


def run_once(range_script: Path, assignment: Path, root: Path) -> dict:
    rebuild = rebuild_range(range_script, assignment, root)
    if rebuild.get("status") != "ready":
        return {"attempt_ok": False, "stage": "rebuild", "detail": rebuild}

    results = run_sequence(range_script, assignment, root, PATH1_SEQUENCE)
    proof_ok = verify_proof(results, assignment, "path_1_proof")

    cleanup_result = run_operation(range_script, assignment, root, "cleanup")

    return {
        "attempt_ok": proof_ok,
        "sequence_results": results,
        "cleanup_result": cleanup_result,
    }


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: path1_automation.py <portable_range.py> <candidate.json> <range-root>")
        sys.exit(1)

    range_script = Path(sys.argv[1])
    assignment = Path(sys.argv[2])
    root = Path(sys.argv[3])

    attempts = []
    for i in range(1, 4):
        attempt = run_once(range_script, assignment, root)
        attempt["attempt_number"] = i
        attempts.append(attempt)

    successes = sum(1 for a in attempts if a["attempt_ok"])
    summary = {
        "path": "path_1",
        "attempts_total": len(attempts),
        "attempts_succeeded": successes,
        "three_of_three": successes == 3,
        "attempts": attempts,
    }
    status = "PASS" if successes == 3 else "FAIL"
    print(f"\n=== PATH 1 SUMMARY: {status} ({successes}/{len(attempts)} clean runs) ===")
    for a in attempts:
        steps = [s.get("operation", "?") + ("OK" if s.get("ok") else "FAIL") for s in a.get("sequence_results", [])]
        print(f"  attempt {a['attempt_number']}: {' -> '.join(steps)}")
    print()

    print(json.dumps(summary, indent=2))
    sys.exit(0 if successes == 3 else 1)


if __name__ == "__main__":
    main()
