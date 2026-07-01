# TICKET-0020: [state.py] Non-atomic file writes risk corruption
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: set_working_html and _write_status write directly to the final file path. If the process crashes mid-write, the file may be left truncated or corrupted, breaking recovery. | Suggestion: Write to a temporary file in the same directory, then atomically rename it to the final path (e.g., pathlib.Path.rename). | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: 
