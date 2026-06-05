# TICKET-0014: Windows console UnicodeEncodeError on emoji in print()
Status: Fixed
Priority: Medium
Type: Bug
Created: 2026-06-05
Description: All scripts using emoji in print() crash on Windows with cp1252 encoding. All print() calls must use ASCII-safe encoding. Affects code_agent.py reviewer output and potentially step7/step8.
Steps to Reproduce: 
Notes: Audited all Scripts/: only step7 had unicode risk (review text). Fixed in new step7_review.py. code_agent.py file writes now use encoding=utf-8.
