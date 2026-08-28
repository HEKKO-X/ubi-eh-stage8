# Windows Events — Not Applicable for This Submission

This stage was completed via the B2 portable route (EH-A4-PORTABLE), which
simulates the AD range as Python-managed JSON state rather than a real
Windows Server Domain Controller. No real Windows Event Log data exists to
collect, since there is no real Windows machine involved.

The equivalent evidence for this route is `ad-range/events.jsonl` (the
range's own action log) and the detection rules built against it — see
`detections/detect.py` and `detections/fixtures/`.

Per the Stage 8 release update, the portable route carries the same
technical rubric as the full GOAD-Light VM route, with no scoring penalty.
