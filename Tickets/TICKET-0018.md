# TICKET-0018: [state.py] Path traversal in run_id
Status: closed
Priority: High
Type: Bug
Created: 2026-06-30
Description: The run_id parameter is used directly as a path component without sanitization, allowing an attacker to create or load runs outside the intended directory (e.g., run_id='../../malicious'). This can lead to arbitrary file read/write if run_id is externally controlled. | Suggestion: Validate run_id against a safe pattern (e.g., re.fullmatch(r'[a-zA-Z0-9_\-]+', run_id)) and raise an error if invalid. Alternatively, derive the directory name from a hash. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
