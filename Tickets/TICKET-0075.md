# TICKET-0075: [state.py] Race condition in atomic write from deterministic temp filename
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: The `_atomic_write_text` helper uses a fixed temporary filename derived from the target path's suffix (e.g. `status.json.tmp`). If two processes or threads call this function concurrently for the same target, they will overwrite each other's temporary file and then both call `os.replace`. The second replace may fail or silently replace with an older version, leading to data corruption. The code's comment only mentions safety for a concurrent reader, but concurrent writers would cause issues. | Suggestion: Generate a unique temporary file per write using a random suffix or the process ID, e.g. `tmp = path.with_suffix(path.suffix + '.' + str(os.getpid()) + '.tmp')`, and clean up any leftover temp files if needed. | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit); suites green.
