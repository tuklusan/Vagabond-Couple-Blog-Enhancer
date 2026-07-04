# TICKET-0149: [state.py] Race condition in status read-modify-write
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: Multiple methods (set_current_node, mark_node) read status.json, modify it, and write it back without any locking. Concurrent calls from different threads can overwrite each other's changes, losing node completion data and corrupting the state. | Suggestion: Add a threading.Lock or a file-based lock (e.g., fcntl) around all _read_status/_write_status pairs to ensure mutual exclusion. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: DUPLICATE, NO ACTION
