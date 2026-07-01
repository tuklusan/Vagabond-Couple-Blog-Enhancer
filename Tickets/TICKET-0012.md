# TICKET-0012: [operator.py] Potential crash on empty options list in choose()
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The choose() method assumes options has at least one element, but if called with an empty list, it will raise IndexError in both auto and interactive branches (e.g., accessing options[default_index] when auto, or after catching exception and returning options[default_index]). This can crash the pipeline if an edge case passes an empty sequence. | Suggestion: Add a guard at the start of choose() to raise a ValueError("options must not be empty") or return a safe sentinel if no options are available. | File: orchestrator/operator.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
