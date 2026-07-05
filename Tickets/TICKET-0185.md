# TICKET-0185: [_review_gate.py] Path traversal allows reading arbitrary files
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: _load_files does not validate that file paths are within the repository, allowing an attacker to specify paths like ../../etc/passwd to exfiltrate sensitive files via the review API. | Suggestion: Resolve paths and ensure they are under REPO using Path.resolve() and relative_to(). | File: .githooks/_review_gate.py | Severity: critical
Steps to Reproduce: 
Notes: VALID AS DEFENSE-IN-DEPTH, FIXED. Exploitability in the actual workflow is near-nil -- the file list comes from the pre-push git hook (git's own changed-file computation), not attacker input, and anyone able to invoke the script with hostile args could read the files directly anyway. But the gate DOES ship file content to an external review API, so confining the list to the repository is cheap, correct hardening. Fixed per the reviewer's suggestion: new `_within_repo(repo, rel_path)` resolves each entry and requires `resolve().relative_to(repo)` + existence (fails closed on ValueError/OSError); `_load_files` drops any non-conforming entry. Tests: test_within_repo_confines_paths (inside allowed, '../' traversal rejected, absolute-outside rejected, missing-inside rejected, redundant-but-inside traversal still allowed).
