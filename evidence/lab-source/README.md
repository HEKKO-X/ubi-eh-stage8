# Stage 8 Portable Directory Range

The portable range is the controlling scored route. It uses only Python's
standard library and does not require GOAD, Windows, a hypervisor, Docker, or a
cloud account.

1. Download your private candidate JSON from the authenticated stage room.
2. Build a clean range:

   `python3 portable_range.py build --assignment candidate.json --out range`

3. Confirm health:

   `python3 portable_range.py health --root range`

4. Treat `range/source-records.json` as primary evidence. Build your own graph,
   validate edges, reject the stale edge, and discover both paths.
5. Your automation may call `portable_range.py act ...`; it must discover names
   and identifiers from the range rather than embed them.
6. Rebuild with `--force` for every clean run. Preserve the initial and final
   manifests, events, automation transcript, cleanup result, and remediation
   negative tests.

`Apply-Variant.ps1` and `Capture-CheckpointMetadata.ps1` remain only for
candidates who already began the optional GOAD compatibility route. The
placeholder `variant.example.json` is never a candidate assignment.
