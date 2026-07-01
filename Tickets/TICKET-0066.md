# TICKET-0066: [__main__.py] Potential path traversal via --run-id
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: The user-supplied --run-id argument is passed directly to RunState.create without sanitization. If it is used to construct a directory path (e.g., state.dir), a crafted value like '../../../etc' could allow writing files outside the intended base directory, leading to data corruption or privilege escalation. | Suggestion: Sanitize run_id to contain only alphanumeric characters, hyphens, and underscores. Reject any value containing path separators or '..' sequences, or replace invalid characters with a safe placeholder. | File: orchestrator/__main__.py | Severity: warning
Steps to Reproduce: 
Notes: run_id already sanitized in RunState (0018); __main__ now catches the ValueError with a friendly 'invalid --run-id' message instead of a traceback.
