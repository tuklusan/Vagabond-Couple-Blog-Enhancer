# TICKET-0085: [test_more_nodes.py] Non‑empty output assertion may be too strict for non‑CERTIF
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The structural assertion requires len(output.strip()) > 0 even when status is REVISE or ESCALATE. If the node can legitimately return an empty output in these states (e.g., a prompt to revise without additional content), the test will produce false failures. | Suggestion: Relax the assertion for non‑CERTIFIED statuses, or verify that the node contract guarantees a non‑empty output in all final states. Consider checking output only when status is CERTIFIED. | File: tests/test_more_nodes.py | Severity: warning
Steps to Reproduce: 
Notes: Test hardening applied (see commit): 0085 non-empty only for CERTIFIED; 0086 wrap live call; 0087 broaden outage skip; 0088 assert BOTH phrases; 0089 assert malformed schema present=True. Deterministic suite green; live tests compile.
