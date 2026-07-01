# TICKET-0102: [test_more_nodes.py] Live test dependency causes flakiness
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: The test calls run_generative_node which interacts with a generative AI provider over the network. Failures can occur due to provider outages, rate limits, network errors, model nondeterminism, or response format changes, making the test unreliable. | Suggestion: Mock the generative node or replace the live test with an integration test using a controlled environment. If live testing is necessary, separate it into a non-essential check (e.g., a nightly build) and skip by default in regular test runs. | File: tests/test_more_nodes.py | Severity: critical
Steps to Reproduce: 
Notes: Duplicate of 0029/0084/0096: test_more_nodes is an intentional LIVE integration test; it already skips on provider outage/rate-limit. Documented as not-for-unattended-CI. No further change.
