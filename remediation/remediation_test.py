#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Remediation verification for both paths.
For each path: prove baseline works, apply remediation, prove the
same sequence now fails at its intended edge, confirm health stays green.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "automation"))
from range_client import rebuild_range, run_sequence, verify_proof, run_operation, check_health

PATH_CONFIG = {
    "path_1": {
        "sequence": ["set-spn", "request-service-token", "read-proof-1"],
        "proof_field": "path_1_proof",
        "remediate_op": "remediate-path-1",
        "expected_blocked_step": "set-spn",
    },
    "path_2": {
        "sequence": ["add-group-member", "read-proof-2"],
        "proof_field": "path_2_proof",
        "remediate_op": "remediate-path-2",
        "expected_blocked_step": "add-group-member",
    },
}


def test_path(path_name: str, range_script: Path, assignment: Path, root: Path) -> dict:
    cfg = PATH_CONFIG[path_name]

    # 1. Clean rebuild
    rebuild_range(range_script, assignment, root)

    # 2. Baseline: attack should still work pre-remediation
    baseline_results = run_sequence(range_script, assignment, root, cfg["sequence"])
    baseline_ok = verify_proof(baseline_results, assignment, cfg["proof_field"])
    run_operation(range_script, assignment, root, "cleanup")

    # 3. Apply remediation
    remediate_result = run_operation(range_script, assignment, root, cfg["remediate_op"])

    # 4. Post-remediation: attack should now fail
    after_results = run_sequence(range_script, assignment, root, cfg["sequence"])
    first_step = after_results[0] if after_results else {}
    blocked_correctly = (
        first_step.get("operation") == cfg["expected_blocked_step"]
        and first_step.get("ok") is False
    )

    # 5. Health must stay green
    health_result = check_health(range_script, root)

    return {
        "path": path_name,
        "baseline_attack_worked": baseline_ok,
        "remediation_applied": remediate_result.get("ok", False),
        "post_remediation_blocked_correctly": blocked_correctly,
        "post_remediation_first_result": first_step,
        "health_after_remediation": health_result.get("healthy", False),
        "pass": baseline_ok and remediate_result.get("ok", False) and blocked_correctly and health_result.get("healthy", False),
    }


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: remediation_test.py <portable_range.py> <candidate.json> <range-root>")
        sys.exit(1)

    range_script = Path(sys.argv[1])
    assignment = Path(sys.argv[2])
    root = Path(sys.argv[3])

    results = {}
    for path_name in ("path_1", "path_2"):
        results[path_name] = test_path(path_name, range_script, assignment, root)

    print("\n=== REMEDIATION TEST SUMMARY ===")
    for path_name, r in results.items():
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  {path_name}: {status}")
        print(f"    baseline attack worked (pre-fix): {r['baseline_attack_worked']}")
        print(f"    remediation applied: {r['remediation_applied']}")
        print(f"    blocked correctly (post-fix): {r['post_remediation_blocked_correctly']}")
        print(f"    health still green: {r['health_after_remediation']}")
    print()

    print(json.dumps(results, indent=2))
    all_pass = all(r["pass"] for r in results.values())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
