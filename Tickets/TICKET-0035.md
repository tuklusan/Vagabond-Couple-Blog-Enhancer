# TICKET-0035: [ticket.py] Path traversal in show_ticket and update_ticket
Status: Open
Priority: High
Type: Bug
Created: 2026-06-30
Description: The show_ticket and update_ticket functions construct file paths by concatenating TICKET_DIR with a user-supplied ticket_id (after optionally prepending 'TICKET-'). A malicious ticket_id like '../../etc/passwd' escapes the Tickets directory, allowing reading or overwriting of arbitrary .md files outside the intended directory. | Suggestion: Sanitize ticket_id to allow only alphanumeric characters and hyphens, or use os.path.basename and verify that the resolved real path is within TICKET_DIR. | File: ticket.py | Severity: critical
Steps to Reproduce: 
Notes: 
