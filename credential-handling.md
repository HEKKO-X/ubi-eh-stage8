# Credential Handling Record

Never place a reusable cleartext credential or full hash in the report, video, public repository, or issue tracker.

| ID | Account type | Source artifact | Storage location | Report representation | Disposal action | UTC disposed |
|---|---|---|---|---|---|---|
| CRED-001 | Foothold user secret | candidate.json (foothold_secret field) | Local file only, git-ignored, not pushed to GitHub | `[REDACTED:last4]` | Retained only in candidate.json for reproducibility during defense; never displayed in full anywhere in this submission | N/A - stays local for defense reproduction, not disposed before grading |
| CRED-002 | Service account secret | candidate.json (service_secret field) | Local file only, git-ignored, not pushed to GitHub | `[REDACTED:last4]` | Retained only in candidate.json for reproducibility during defense; never displayed in full anywhere in this submission | N/A - stays local for defense reproduction, not disposed before grading |
| CRED-003 | Path 1 proof value | candidate.json (path_1_proof), automation/path1-run-log.json | Local files only, in this submission folder's evidence subdirectories | `[REDACTED]` in README.md, attack-paths.json, and continuity-record.md; visible only in raw run logs | Not disposed - required as raw evidence for grading verification | N/A |
| CRED-004 | Path 2 proof value | candidate.json (path_2_proof), automation/path2-run-log.json | Local files only, in this submission folder's evidence subdirectories | `[REDACTED]` in README.md, attack-paths.json, and continuity-record.md; visible only in raw run logs | Not disposed - required as raw evidence for grading verification | N/A |

I confirm the credential material came only from the assigned lab (candidate.json,
marker UBI-A8-D426CF231FB6) and was not tested against any other system.

Note on candidate.json itself: this file is intentionally excluded from the
version-controlled repository (see .gitignore) per this same credential
handling discipline, since committing it would place reusable secrets into
git history permanently. It is included in the Google Drive submission
folder as required, but grader access to the folder should still be treated
as sensitive per program norms.

Signed: Kazeem Habeeb
UTC date/time: Fri Aug 28 05:46:09 AM UTC 2026
