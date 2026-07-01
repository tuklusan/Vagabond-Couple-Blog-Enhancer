# TICKET-0036: [ticket.py] Newline injection in ticket creation breaks file format
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The create_ticket_file function inserts user-supplied args.title, args.desc, and other fields directly into the ticket file lines without sanitization. If any field contains newline characters, it can inject arbitrary lines into the file, corrupting the structure and allowing fake metadata to be added or the ticket to become unparseable. | Suggestion: Strip or replace newline characters from all user-supplied input before writing to the file. | File: ticket.py | Severity: warning
Steps to Reproduce: 
Notes: 
