# TICKET-0032: [test_node_loop.py] Verdict check assumes 'decision' key always present
Status: closed
Priority: High
Type: Task
Created: 2026-06-30
Description: The assertion 'verdict_has_decision' requires outcome['verdict'] to be a dict containing 'decision'. However, if the status is 'ESCALATE', the verdict might be absent or not contain 'decision', leading to false failures. | Suggestion: Make this check conditional on the status, e.g., only assert verdict has decision if status in ('CERTIFIED', 'REVISE'), or verify the expected structure based on the actual outcome. | File: tests/test_node_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic suites green; live tests compile + made outage-robust.
