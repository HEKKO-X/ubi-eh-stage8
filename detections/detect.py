#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Detection engine: reads a JSONL event log (real or a replay fixture)
and evaluates two detection rules against it.
"""
import json
import sys
from pathlib import Path


def load_events(path: Path) -> list:
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def detect_spn_abuse_chain(events: list) -> dict:
    """
    Detection 1: same actor completes set-spn -> request-service-token
    -> read-proof-1, all successful, in that order.
    An incomplete chain (e.g. only set-spn, no follow-through) does NOT alert.
    """
    by_actor = {}
    for e in events:
        by_actor.setdefault(e.get("actor"), []).append(e)

    for actor, actor_events in by_actor.items():
        seen = {"set-spn": False, "request-service-token": False, "read-proof-1": False}
        order = []
        for e in actor_events:
            action = e.get("action")
            if action in seen and e.get("result") == "success":
                seen[action] = True
                order.append(action)
        chain_complete = all(seen.values())
        correct_order = order[:3] == ["set-spn", "request-service-token", "read-proof-1"]
        if chain_complete and correct_order:
            return {"rule": "spn_abuse_chain", "alert": True, "actor": actor, "evidence": order}

    return {"rule": "spn_abuse_chain", "alert": False, "evidence": []}


def detect_group_selfadd_chain(events: list) -> dict:
    """
    Detection 2: same actor completes add-group-member -> read-proof-2,
    both successful, in order. A group-add targeting something other
    than the sensitive group, with no follow-up read-proof-2, does NOT alert.
    """
    by_actor = {}
    for e in events:
        by_actor.setdefault(e.get("actor"), []).append(e)

    for actor, actor_events in by_actor.items():
        seen = {"add-group-member": False, "read-proof-2": False}
        order = []
        for e in actor_events:
            action = e.get("action")
            if action in seen and e.get("result") == "success":
                seen[action] = True
                order.append(action)
        chain_complete = all(seen.values())
        correct_order = order[:2] == ["add-group-member", "read-proof-2"]
        if chain_complete and correct_order:
            return {"rule": "group_selfadd_chain", "alert": True, "actor": actor, "evidence": order}

    return {"rule": "group_selfadd_chain", "alert": False, "evidence": []}


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: detect.py <events.jsonl>")
        sys.exit(1)

    events_path = Path(sys.argv[1])
    events = load_events(events_path)

    result1 = detect_spn_abuse_chain(events)
    result2 = detect_group_selfadd_chain(events)

    output = {"source_file": str(events_path), "detections": [result1, result2]}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
