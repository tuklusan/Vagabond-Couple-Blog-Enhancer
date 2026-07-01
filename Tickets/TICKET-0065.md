# TICKET-0065: [README.md] Contradictory href preservation claim
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The 'What it does' section claims to 'remove ?m=1 from internal links — while preserving every original href byte-for-byte.' Removing ?m=1 would change the bytes of those links, making it impossible to preserve all hrefs byte-for-byte. This contradiction can confuse users about the tool's behavior. | Suggestion: Rephrase to: 'remove ?m=1 from internal links, while preserving all other original hrefs byte-for-byte.' | File: README.md | Severity: warning
Steps to Reproduce: 
Notes: README reworded: '?m=1 stripping is the one intentional audited href change; all OTHER hrefs preserved byte-for-byte'.
