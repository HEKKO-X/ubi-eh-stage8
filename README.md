# Stage 8 — Own the Forest — README

## Candidate

- Intern code: UBI-2026-0052
- Track: Ethical Hacking
- Variant: D1
- Evidence marker: UBI-A8-D426CF231FB6
- Project: EH-A4-PORTABLE (portable route, per Stage 8 controlling release update)

## Tool and OS versions

| Tool | Version |
|---|---|
| OS | Kali GNU/Linux Rolling |
| Architecture | x86_64 |
| Python | 3.13.3 |

## Folder structure

- ad-range/          built range (state.json, source-records.json, events.jsonl, manifest.json)
- enumeration/       discover.py, discovery-output.json
- automation/        range_client.py, path1_automation.py, path2_automation.py, run logs
- detections/        detect.py, fixtures/, test results
- remediation/       remediation_test.py, run log
- windows-events/    not used - portable route has no Windows event logs
- evidence/          hashes, build logs, source materials
- candidate.json     assigned candidate file (private - contains secrets, not for public sharing)
- README.md          this file

## Exact reproduction order

Run all commands from `~/eh-stage8`. Each step's real output is logged under `evidence/`.

### 1. Build and verify the range

```bash
python3 evidence/lab-source/portable_range.py build --assignment candidate.json --out ad-range --force
python3 evidence/lab-source/portable_range.py health --root ad-range
shasum -a 256 candidate.json ad-range/manifest.json
```

### 2. Run enumeration / discovery

```bash
python3 enumeration/discover.py ad-range/source-records.json candidate-b6214a7d
```

Output: `enumeration/discovery-output.json` — all 9 graph edges classified, both attack paths discovered, 1 stale edge correctly rejected.

### 3. Run Path 1 automation (credential abuse + ACL edge)

```bash
python3 automation/path1_automation.py evidence/lab-source/portable_range.py candidate.json ad-range
```

Sequence: `set-spn -> request-service-token -> read-proof-1 -> cleanup`
Result: 3 of 3 clean runs succeeded, real proof verified each time.

### 4. Run Path 2 automation (pure ACL abuse)

```bash
python3 automation/path2_automation.py evidence/lab-source/portable_range.py candidate.json ad-range
```

Sequence: `add-group-member -> read-proof-2 -> cleanup`
Result: 3 of 3 clean runs succeeded, real proof verified each time.

### 5. Run remediation verification (both paths)

```bash
python3 remediation/remediation_test.py evidence/lab-source/portable_range.py candidate.json ad-range
```

Proves: attack works before fix, remediation applies, same attack fails at intended edge afterward, range health stays green.

**Note:** this step permanently marks the range as remediated. Rebuild with `--force` afterward if further attack testing is needed.

### 6. Run detection tests

```bash
for f in detections/fixtures/*.jsonl; do
  python3 detections/detect.py "$f"
done
```

Two rules: `spn_abuse_chain` and `group_selfadd_chain`. Both alert correctly on positive fixtures and real captured attack logs, and stay silent on benign fixtures.

## Known limitations

- `events.jsonl` is reset on every `build --force` call; it only reflects the most recent build cycle, not cumulative history across separate script runs. Detection was verified against isolated single-path runs to produce a clean real-data trace for each rule.
- The optional full GOAD-Light VM route was not used — this submission follows the controlling B2 portable pack route, per the Stage 8 release update dated 2026-08-19 stating no hardware bonus applies and the portable route carries the same rubric.

## Credential handling

Real secrets and proof values are held only in `candidate.json` and local run logs under `automation/` and `remediation/`, kept in this local, non-public evidence folder. They are not reproduced in this README or in `decision-log.md`. See `credential-handling-record.md` for full disposal record.
