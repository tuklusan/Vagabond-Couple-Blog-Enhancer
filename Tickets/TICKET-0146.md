# TICKET-0146: [state.py] TOCTOU race condition in status file updates
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: `_read_status` followed by `_write_status` in `set_current_node` and `mark_node` is not protected by locking. Concurrent threads/processes can interleave reads and writes, leading to lost updates and corruption of `status.json` (e.g., losing node completion records). This breaks the durable run state contract. | Suggestion: Add a file‑based lock (e.g., `fcntl.flock`, `portalocker`, or a dedicated lockfile) around the read‑modify‑write operation on `status_path`. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: Accepted-design, not fixed: the orchestrator's actual execution model is strictly single-threaded, sequential node-by-node (verified throughout this session -- no threading/multiprocessing anywhere drives concurrent access to status.json). The suggested fix (fcntl.flock) is POSIX-only and does not work on this project's actual platform (Windows, per system info); a real fix would need a cross-platform locking dependency (e.g. portalocker) not currently used anywhere in the project, to guard against a race that cannot occur in any current code path. Disproportionate to actual risk -- deferred. Revisit if/when the orchestrator ever runs multiple nodes/runs concurrently against the same run_id (it currently never does).
