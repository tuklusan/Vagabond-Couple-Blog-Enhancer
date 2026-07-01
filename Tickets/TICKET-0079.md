# TICKET-0079: [validators.py] False positives in scan_question_marks
Status: Open
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: The regex r"(?<=\w)\?|\?(?=\w)" in scan_question_marks() catches any '?' that is adjacent to a word character on either side, which includes legitimate punctuation at sentence ends (e.g., 'What?'). This causes many false positives, incorrectly flagging files as suspect. | Suggestion: Use r"(?<=\w)\?(?=\w)" to require a word character on both sides of the '?', ensuring only embedded (within-word) question marks are flagged. | File: orchestrator/validators.py | Severity: warning
Steps to Reproduce: 
Notes: 
