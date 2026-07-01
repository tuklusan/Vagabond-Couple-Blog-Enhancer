# TICKET-0087: [test_node_loop.py] Incomplete skip logic for external service outages
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The test only skips on ESCALATE with reason containing 'writer_unavailable'. If the reviewer or both services are unavailable, the test will fail even though the root cause is an external outage, leading to flaky failures in CI. | Suggestion: Either skip on any ESCALATE status that is due to external unavailability (e.g., check for keywords like 'unavailable' or 'error' in the reason) or treat all ESCALATE outcomes as skippable if the test cannot differentiate external vs. internal failures. | File: tests/test_node_loop.py | Severity: warning
Steps to Reproduce: 
Notes: Test hardening applied (see commit): 0085 non-empty only for CERTIFIED; 0086 wrap live call; 0087 broaden outage skip; 0088 assert BOTH phrases; 0089 assert malformed schema present=True. Deterministic suite green; live tests compile.
