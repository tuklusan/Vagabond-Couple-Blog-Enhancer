# TICKET-0031: [test_node_loop.py] Fragile content assertions flaky on model variance
Status: closed
Priority: High
Type: Task
Created: 2026-06-30
Description: The test checks for exact lowercased substrings 'ashgabat' and 'turkmenbashi' in the LLM output. Even with case-insensitivity, the model may paraphrase or omit these terms, causing false failures. This contradicts the claim that the test only asserts structural invariants. | Suggestion: Replace content checks with structural assertions, e.g., verify output is a non-empty string and status is valid. If content validation is needed, use a mock to control the output or assert presence of key entities using NLP techniques tolerant of variation. | File: tests/test_node_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic suites green; live tests compile + made outage-robust.
