# TICKET-0146: [state.py] TOCTOU race condition in status file updates
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: `_read_status` followed by `_write_status` in `set_current_node` and `mark_node` is not protected by locking. Concurrent threads/processes can interleave reads and writes, leading to lost updates and corruption of `status.json` (e.g., losing node completion records). This breaks the durable run state contract. | Suggestion: Add a file‑based lock (e.g., `fcntl.flock`, `portalocker`, or a dedicated lockfile) around the read‑modify‑write operation on `status_path`. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: DUPLICATE, NO ACTION
