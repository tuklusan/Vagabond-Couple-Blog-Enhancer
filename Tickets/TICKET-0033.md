# TICKET-0033: [test_node_loop.py] Bare dictionary accesses may cause KeyError
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The test accesses outcome['output'] and outcome['history'] without verifying the keys exist, risking unhandled KeyError if the response structure changes. | Suggestion: Use outcome.get('output', '') and outcome.get('history', []) or validate the response structure upfront. | File: tests/test_node_loop.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic suites green; live tests compile + made outage-robust.
