# TICKET-0029: [test_more_nodes.py] Live generative node test is non-deterministic and flaky
Status: Open
Priority: High
Type: Task
Created: 2026-06-30
Description: The test runs actual generative nodes via orchestrator.review_loop, which depends on external LLM services and randomness. This makes the test pass or fail inconsistently depending on external API availability, latency, and model outputs. It fails test isolation and determinism requirements. | Suggestion: Replace live node calls with deterministic mocks or stubs that return controlled outputs, or separate integration tests into a dedicated environment with stable expectations. | File: tests/test_more_nodes.py | Severity: critical
Steps to Reproduce: 
Notes: 
