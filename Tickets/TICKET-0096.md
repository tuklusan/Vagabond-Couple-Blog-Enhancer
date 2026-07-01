# TICKET-0096: [test_more_nodes.py] Overly broad provider-outage skip may suppress real failure
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: The outage skip matches a wide set of keywords in the reason string ('unavailable', 'outage', 'rate', '429', 'timed out', 'timeout', 'failed'). This can cause legitimate test failures that happen to contain these words to be silently skipped, hiding real bugs. | Suggestion: Use a more specific, structured error code or a dedicated exception class to distinguish provider outages from other failures. Alternatively, refactor the live test to run in a controlled environment with deterministic responses. | File: tests/test_more_nodes.py | Severity: critical
Steps to Reproduce: 
Notes: Addressed: narrowed the live-test outage skip to specific markers (unavailable/outage/rate/429/timeout), removing generic 'failed'/'error' that could mask real failures (test_node_loop + test_more_nodes).
