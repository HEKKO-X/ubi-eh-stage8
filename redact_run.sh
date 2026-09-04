#!/usr/bin/env bash
# Wraps any command and masks known secret/proof values before printing.
# Usage: ./redact_run.sh python3 automation/path1_automation.py ...
SECRETS_FILE="candidate.json"
mapfile -t VALUES < <(python3 -c "
import json
d = json.load(open('$SECRETS_FILE'))
for k in ('foothold_secret','service_secret','path_1_proof','path_2_proof'):
    print(d[k])
")

OUTPUT=$("$@" 2>&1)
for v in "${VALUES[@]}"; do
    OUTPUT="${OUTPUT//$v/[REDACTED]}"
done
echo "$OUTPUT"
