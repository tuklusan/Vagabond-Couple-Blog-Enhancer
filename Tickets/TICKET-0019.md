# TICKET-0019: [state.py] Race condition on status.json
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: Methods set_current_node and mark_node perform a read-modify-write cycle on status.json without any locking. Concurrent calls (e.g., multiple processes or threads) can interleave, leading to lost updates or corrupted status. | Suggestion: Use file-based locking (e.g., a companion '.lock' file and fcntl) or enforce single-writer access. If only one writer is expected, document that the class is not thread/process-safe. | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: 
