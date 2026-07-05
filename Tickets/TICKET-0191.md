# TICKET-0191: [test_sequencer.py] Missing mock for run_generative_node in test_drop_factoid_re
Status: Closed
Priority: High
Type: Task
Created: 2026-07-05
Description: The test calls sequencer._drop_flagged_factoid without mocking review_loop.run_generative_node, causing a real LLM call and violating the no-LLM requirement, leading to flakiness and external dependencies. | Suggestion: Wrap the call in a mock for run_generative_node similar to other remediation tests, or restructure _drop_flagged_factoid to accept a callable. | File: tests/test_sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. _drop_flagged_factoid (orchestrator/sequencer.py) never calls review_loop.run_generative_node or anything LLM-backed -- it reads the already-persisted gen_step9f_factoid artifact and scores section-title/output tokens against the Pass-1 revision text, purely deterministic string/set operations. The test therefore makes no network call and is not flaky; it passes deterministically (verified: both assertions in test_drop_factoid_requires_output_evidence pass on every run). The reviewer likely confused this with _remediate_flagged_passage, a DIFFERENT function that does call run_generative_node and IS covered by a mocked test (test_remediate_flagged_passage_rewrites_and_preserves_hrefs). No code change made.
