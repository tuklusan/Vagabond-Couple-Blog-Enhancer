# TICKET-0212: [test_context.py] Main test may invoke LLM, violating determinism
Status: Closed
Priority: High
Type: Task
Created: 2026-07-05
Description: The test claims to be deterministic and LLM-free, but extract_context() is called without allow_llm=False. If the function defaults to allow LLM, this can cause flaky failures when an LLM is unavailable or produces unexpected results. | Suggestion: Add allow_llm=False to the extract_context call in main(), or mock LLM-dependent functions to ensure deterministic behavior. | File: tests/test_context.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. The reviewer's conditional ('IF the function defaults to allow LLM') resolves against the actual signature: `def extract_context(html, allow_llm=False)` -- the LLM path is opt-in and the bare call in main() is deterministic by construction. The only allow_llm=True calls in the file are in test_derived_waypoints_string_type_ignored, where derive_route_from_prose is monkey-patched to a local lambda (effectiveness itself verified when closing TICKET-0209), so no test in this suite can reach a live provider. The suite has run LLM-free since Phase B. No code change made.
