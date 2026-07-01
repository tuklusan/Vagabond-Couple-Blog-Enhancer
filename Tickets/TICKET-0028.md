# TICKET-0028: [test_document_cert.py] Weak assertion for hrefs_preserved defaults to True
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The check `c.get('hrefs_preserved', True)` passes even if the key is missing. If the checklist implementation incorrectly omits this key, the test would still pass, potentially hiding a regression. | Suggestion: Change to `check('hrefs_preserved', c.get('hrefs_preserved') is True)` to assert the key exists and is True. | File: tests/test_document_cert.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic suites green; live tests compile + made outage-robust.
