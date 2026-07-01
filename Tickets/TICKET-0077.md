# TICKET-0077: [state.py] `RunState.create` silently overwrites an existing run
Status: Open
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: The `create` classmethod writes the initial working HTML and status directly without checking if a run with the same `run_id` already exists. While auto-generated run IDs are unlikely to collide, a user-supplied `run_id` could accidentally re-create an existing run, losing all previous artifacts and status. This violates the principle of least surprise and could cause data loss. | Suggestion: Add an existence check before creating the run directory and raise an error (or at least warn) if the directory already contains a `status.json`. For example, test `(self.dir / 'status.json').exists()` and raise `FileExistsError` with a clear message. | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: 
