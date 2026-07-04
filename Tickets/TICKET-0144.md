# TICKET-0144: [state.py] Non-unique temp file name causes data corruption under concurrency
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: _atomic_write_text uses PID as part of the temp file name to avoid clobbering across processes, but within the same process multiple threads will share the same PID, leading to simultaneous writes to the same temp file and potential corruption of working HTML, status, or artifacts. | Suggestion: Include the thread id (`threading.get_ident()`) or a random component (e.g., `uuid4().hex`) in the temp filename to make it unique per concurrent writer. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: _atomic_write_text's temp filename now includes threading.get_ident() alongside the existing pid, so concurrent threads within the same process (sharing one pid) can no longer collide on the same temp file.
