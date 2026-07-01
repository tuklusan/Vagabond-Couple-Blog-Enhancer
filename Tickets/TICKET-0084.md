# TICKET-0084: [test_more_nodes.py] Live test depends on external services, may be flaky
Status: Open
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The test calls generative nodes via review_loop, which depends on external API providers. Only a specific 'writer_unavailable' error is skipped; other transient failures (network issues, rate limits, provider partial outages) will cause deterministic failures, reducing test reliability. | Suggestion: Either mock node interfaces for deterministic CI runs, implement a retry mechanism, or broaden the skip conditions to cover common provider outages (e.g., any ESCALATE due to external service errors). Alternatively, document that the test is expected to be run manually and not in automated pipelines. | File: tests/test_more_nodes.py | Severity: warning
Steps to Reproduce: 
Notes: 
