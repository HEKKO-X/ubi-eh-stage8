#!/usr/bin/env python3
"""
Stage 8 - Own the Forest
Dynamic AD graph discovery.
Reads source-records.json, builds a graph, walks it from the
foothold user, and classifies every edge.
No hardcoded names/IDs/flags - everything is read at runtime.
"""
import json
import sys
from pathlib import Path

def load_records(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(records: dict) -> dict:
    """
    Turns the flat objects/relations lists into something we can walk:
    - a lookup of every known object name -> its type
    - an adjacency list: source name -> list of edge dicts
    """
    objects_by_name = {}
    for obj in records.get("objects", []):
        objects_by_name[obj["name"]] = obj

    adjacency = {}
    for rel in records.get("relations", []):
        src = rel["source"]
        adjacency.setdefault(src, []).append(rel)

    return {
        "objects_by_name": objects_by_name,
        "adjacency": adjacency,
    }


def find_foothold(objects_by_name: dict) -> str:
    """
    Finds the foothold user WITHOUT hardcoding a name.
    Rule: the foothold is the 'user' type object that has at least
    one outgoing edge but is not itself a target of any privileged edge
    from another identity. Simpler, safe approach for this range:
    the candidate JSON tells us at build time, but discovery must not
    depend on that file - so we treat the foothold as an explicit
    runtime argument instead of guessing it from shape alone.
    """
    raise NotImplementedError("foothold is passed in explicitly - see main()")


def edge_validity(edge: dict, objects_by_name: dict) -> tuple[bool, str]:
    """
    Decides if an edge can be trusted.
    Returns (is_valid, reason).
    """
    if edge.get("stale") is True:
        return False, "marked_stale"

    target_name = edge.get("target")
    target_obj = objects_by_name.get(target_name)
    if target_obj is None:
        return False, "target_object_missing"

    if target_obj.get("enabled") is False:
        return False, "target_disabled"

    return True, "valid"


def walk_graph(foothold: str, graph: dict) -> dict:
    """
    Breadth-first walk from the foothold, following only valid edges.
    Classifies EVERY relation in the raw data, not just ones the walk
    happens to touch - edges whose source is never reachable are still
    reported, tagged source_reachable=False.
    Returns:
      - reachable: set of object names controllable from foothold
      - parent_edge: maps object name -> the valid edge used to first reach it
      - all_edges_classified: every edge with its validity verdict
    """
    adjacency = graph["adjacency"]
    objects_by_name = graph["objects_by_name"]

    reachable = {foothold}
    parent_edge = {}
    queue = [foothold]

    while queue:
        current = queue.pop(0)
        for edge in adjacency.get(current, []):
            valid, reason = edge_validity(edge, objects_by_name)
            if valid and current in reachable:
                target = edge["target"]
                if target not in reachable:
                    reachable.add(target)
                    parent_edge[target] = edge
                    queue.append(target)

    all_edges_classified = []
    for source_name, edges in adjacency.items():
        for edge in edges:
            valid, reason = edge_validity(edge, objects_by_name)
            record = dict(edge)
            record["source_reachable"] = source_name in reachable
            record["valid"] = valid if source_name in reachable else False
            record["reason"] = reason if source_name in reachable else "source_unreachable"
            all_edges_classified.append(record)

    return {
        "reachable": reachable,
        "parent_edge": parent_edge,
        "all_edges_classified": all_edges_classified,
    }


def extract_path_to(target: str, parent_edge: dict, foothold: str) -> list:
    """
    Walks backward from a proof object to the foothold using
    parent_edge, then reverses it into foothold -> ... -> target order.
    Returns a list of edge dicts, or [] if target was never reached.
    """
    if target not in parent_edge and target != foothold:
        return []

    chain = []
    current = target
    while current != foothold:
        edge = parent_edge.get(current)
        if edge is None:
            return []
        chain.append(edge)
        current = edge["source"]

    chain.reverse()
    return chain


def find_proof_objects(objects_by_name: dict) -> list:
    """Finds every object of type 'proof', by type - not by name."""
    return [
        obj["name"] for obj in objects_by_name.values()
        if obj.get("type") == "proof"
    ]


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: discover.py <source-records.json> <foothold-username>")
        sys.exit(1)

    records_path = Path(sys.argv[1])
    foothold = sys.argv[2]

    records = load_records(records_path)
    graph = build_graph(records)

    if foothold not in graph["objects_by_name"]:
        print(f"ERROR: foothold '{foothold}' not found in objects", file=sys.stderr)
        sys.exit(1)

    result = walk_graph(foothold, graph)
    proofs = find_proof_objects(graph["objects_by_name"])

    output = {
        "marker": records.get("marker"),
        "foothold": foothold,
        "reachable_objects": sorted(result["reachable"]),
        "edges_classified": result["all_edges_classified"],
        "discovered_paths": {},
    }

    for proof in proofs:
        chain = extract_path_to(proof, result["parent_edge"], foothold)
        output["discovered_paths"][proof] = [
            {"source": e["source"], "edge": e["edge"], "target": e["target"]}
            for e in chain
        ]

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
