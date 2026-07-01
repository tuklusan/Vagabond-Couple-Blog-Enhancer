# TICKET-0025: [test_assembler.py] Weak assertion for separator placement
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The test only checks that 'SEPARATOR' appears in the output but does not verify it is placed between the two table blocks, potentially missing insertion position bugs. | Suggestion: Assert a specific order: first table, then separator, then second table using string positions or regex. | File: tests/test_assembler.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic suites green; live tests compile + made outage-robust.
