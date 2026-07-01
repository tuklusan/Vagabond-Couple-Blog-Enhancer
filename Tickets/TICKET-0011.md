# TICKET-0011: [nodes.py] ETR format validation is insufficient
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The description deterministic check only ensures 'ETR' substring is present, but does not verify the required 'ETR: N min' pattern. A writer could output 'ETR:  min' (missing number) and still pass the check, potentially leading to invalid search descriptions. | Suggestion: Change the check to use a regex like r'ETR:\s*\d+\s*min' to enforce the correct format and avoid missing numbers. | File: orchestrator/nodes.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
