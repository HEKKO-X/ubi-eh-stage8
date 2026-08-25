# Advanced Project 4 Integrity Attestation

Intern code: UBI-2026-0052
Variant: D1
Evidence marker: UBI-A8-D426CF231FB6

I attest that I performed the submitted work on the assigned authorized
artifacts (portable_range.py, candidate.json — marker UBI-A8-D426CF231FB6).
I have declared material assistance below and can reproduce the work
during recorded defense. I did not alter raw evidence, fabricate tool
output, rewrite commit history, share restricted artifacts, or cross scope.

## Assistance and tools used

I used Claude (Anthropic AI assistant) throughout this project as a
learning and drafting aid. Specifically:

- Claude explained Active Directory, Kerberos, and ACL concepts I had
  no prior background in, before any hands-on work began.
- Claude helped me interpret the raw source-records.json graph data;
  I then manually traced both attack paths by hand in conversation
  before any automation was written, to confirm I understood the
  logic myself.
- Claude co-wrote enumeration/discover.py, automation/range_client.py,
  automation/path1_automation.py, automation/path2_automation.py,
  remediation/remediation_test.py, and detections/detect.py with me,
  proposing code which I then typed/ran myself on my own Kali VM,
  reviewed, and confirmed the output of at each step.
- Claude identified a real bug in my first enumeration script (it
  silently dropped an unreachable-source edge) and proposed the fix,
  which I applied and re-verified.
- Claude helped draft this documentation set (README.md,
  decision-log.md, evidence-index.csv, this attestation, and the
  continuity record), based on real command output I generated and
  pasted back for review.
- All commands were executed by me, on my own machine, against my own
  assigned candidate.json. All proof values, hashes, and test results
  in this submission come from my own real runs, not from Claude.
- I take full responsibility for every technical claim in this
  submission and can reproduce, explain, and defend each step live.

Signed name: Kazeem Habeeb
UTC date/time: Tue Aug 25 08:37:11 PM UTC 2026

