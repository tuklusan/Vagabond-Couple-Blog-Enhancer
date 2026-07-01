# TICKET-0037: [ticket.py] Race condition in ticket ID generation
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: get_next_ticket_id reads the highest existing ticket ID from the filesystem and then creates a new file with the next ID. If multiple processes run concurrently, they can obtain the same next ID, leading to overwrites or duplicate IDs that corrupt data. | Suggestion: Use file locking or atomic file creation (e.g., open with O_EXCL or rename a temporary file) to ensure exclusive access, or maintain a centralized ID counter with proper synchronization. | File: ticket.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
