#!/usr/bin/env python3
"""Small deterministic directory control plane for the scored Stage 8 route."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def assignment(path: Path) -> dict:
    value = read_json(path)
    required = {
        "schema_version", "project", "intern_code", "variant", "marker",
        "candidate_binding", "foothold_user", "foothold_secret", "service_user",
        "service_secret", "path_1_proof", "path_2_proof",
    }
    missing = sorted(required - value.keys())
    if missing or value.get("project") != "EH-A4-PORTABLE":
        raise SystemExit(f"invalid candidate JSON; missing={missing}")
    return value


def initial_state(a: dict) -> dict:
    sid = digest(a["candidate_binding"])
    candidate = a["foothold_user"]
    service = a["service_user"]
    return {
        "schema_version": "2.0",
        "binding": a["candidate_binding"],
        "marker": a["marker"],
        "variant": a["variant"],
        "objects": [
            {"id": f"U-{sid}-01", "type": "user", "name": candidate, "enabled": True},
            {"id": f"U-{sid}-02", "type": "user", "name": service, "enabled": True, "spns": []},
            {"id": f"G-{sid}-01", "type": "group", "name": "Archive Operators", "members": []},
            {"id": f"G-{sid}-02", "type": "group", "name": "Directory Administrators", "members": []},
            {"id": f"C-{sid}-01", "type": "computer", "name": "FILE01", "enabled": True},
            {"id": f"P-{sid}-01", "type": "proof", "name": "archive-primary"},
            {"id": f"P-{sid}-02", "type": "proof", "name": "archive-secondary"},
        ],
        "relations": [
            {"source": candidate, "edge": "WriteSPN", "target": service, "source_record": "ACL-01"},
            {"source": candidate, "edge": "GenericAll", "target": "Archive Operators", "source_record": "ACL-02"},
            {"source": service, "edge": "CanAuthenticate", "target": "FILE01", "source_record": "AUTH-01"},
            {"source": service, "edge": "ReadProof", "target": "archive-primary", "source_record": "FILE-ACL-01"},
            {"source": "Archive Operators", "edge": "ReadProof", "target": "archive-secondary", "source_record": "FILE-ACL-02"},
            {"source": "Archive Operators", "edge": "RemoteInteractiveLogon", "target": "FILE01", "source_record": "RIGHT-01"},
            {"source": "Directory Administrators", "edge": "AdminTo", "target": "FILE01", "source_record": "LOCAL-01"},
            {"source": service, "edge": "MemberOf", "target": "Service Accounts", "source_record": "MEMBER-01"},
            {"source": candidate, "edge": "GenericAll", "target": "deleted-group", "source_record": "STALE-01", "stale": True},
        ],
        "temporary": {"spn_added": False, "group_member_added": False, "service_token": False},
        "remediated": {"path_1": False, "path_2": False},
        "event_sequence": 0,
    }


def emit_event(root: Path, state: dict, action: str, actor: str, target: str, result: str) -> None:
    state["event_sequence"] += 1
    event = {
        "sequence": state["event_sequence"],
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "action": action,
        "actor": actor,
        "target": target,
        "result": result,
    }
    with (root / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def save(root: Path, state: dict) -> None:
    write_json(root / "state.json", state)


def build(args: argparse.Namespace) -> None:
    a = assignment(args.assignment)
    if args.out.exists():
        if not args.force:
            raise SystemExit(f"refusing to overwrite {args.out}; use --force for a clean reset")
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)
    state = initial_state(a)
    save(args.out, state)
    (args.out / "events.jsonl").write_text("", encoding="utf-8")
    write_json(args.out / "source-records.json", {
        "objects": state["objects"], "relations": state["relations"], "marker": state["marker"]
    })
    manifest = {}
    for name in ("state.json", "events.jsonl", "source-records.json"):
        manifest[name] = hashlib.sha256((args.out / name).read_bytes()).hexdigest()
    write_json(args.out / "manifest.json", manifest)
    print(json.dumps({"status": "ready", "variant": state["variant"], "marker": state["marker"]}))


def health(args: argparse.Namespace) -> None:
    state = read_json(args.root / "state.json")
    objects = {item["name"] for item in state["objects"]}
    checks = {
        "binding_present": bool(state.get("binding")),
        "marker_present": bool(state.get("marker")),
        "candidate_present": any(name.startswith("candidate-") for name in objects),
        "service_present": any(name.startswith("svc-archive-") for name in objects),
        "proof_objects_present": {"archive-primary", "archive-secondary"}.issubset(objects),
        "stale_edge_present": any(row.get("stale") for row in state["relations"]),
    }
    print(json.dumps({"healthy": all(checks.values()), "checks": checks}, indent=2, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


def act(args: argparse.Namespace) -> None:
    state = read_json(args.root / "state.json")
    a = assignment(args.assignment)
    actor = a["foothold_user"]
    result: dict[str, object] = {"operation": args.operation, "ok": False}
    if args.operation == "set-spn" and not state["remediated"]["path_1"]:
        state["temporary"]["spn_added"] = True
        result["ok"] = True
    elif args.operation == "request-service-token" and state["temporary"]["spn_added"]:
        state["temporary"]["service_token"] = True
        result["ok"] = True
    elif args.operation == "read-proof-1" and state["temporary"]["service_token"]:
        result.update({"ok": True, "proof": a["path_1_proof"]})
    elif args.operation == "add-group-member" and not state["remediated"]["path_2"]:
        state["temporary"]["group_member_added"] = True
        result["ok"] = True
    elif args.operation == "read-proof-2" and state["temporary"]["group_member_added"]:
        result.update({"ok": True, "proof": a["path_2_proof"]})
    elif args.operation == "cleanup":
        state["temporary"] = {"spn_added": False, "group_member_added": False, "service_token": False}
        result["ok"] = True
    elif args.operation == "remediate-path-1":
        state["remediated"]["path_1"] = True
        state["temporary"]["spn_added"] = False
        state["temporary"]["service_token"] = False
        result["ok"] = True
    elif args.operation == "remediate-path-2":
        state["remediated"]["path_2"] = True
        state["temporary"]["group_member_added"] = False
        result["ok"] = True
    emit_event(args.root, state, args.operation, actor, args.operation, "success" if result["ok"] else "denied")
    save(args.root, state)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("--assignment", type=Path, required=True)
    p_build.add_argument("--out", type=Path, required=True)
    p_build.add_argument("--force", action="store_true")
    p_build.set_defaults(func=build)
    p_health = sub.add_parser("health")
    p_health.add_argument("--root", type=Path, required=True)
    p_health.set_defaults(func=health)
    p_act = sub.add_parser("act")
    p_act.add_argument("--assignment", type=Path, required=True)
    p_act.add_argument("--root", type=Path, required=True)
    p_act.add_argument("operation", choices=(
        "set-spn", "request-service-token", "read-proof-1", "add-group-member",
        "read-proof-2", "cleanup", "remediate-path-1", "remediate-path-2",
    ))
    p_act.set_defaults(func=act)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
