# TICKET-0182: [test_sequencer.py] test_resume_skips_completed_nodes depends on unpersisted sta
Status: Closed
Priority: High
Type: Task
Created: 2026-07-04
Description: The test calls RunState.load('test_resume') after RunState.create(...) without explicitly persisting the state. If RunState.create does not automatically save to disk, the load will fail or return an empty state, causing the resume test to be ineffective and likely flaky. This also breaks test isolation by relying on file-system side effects. | Suggestion: Ensure the state is persisted (e.g., call state.save()) before loading, or refactor to use an in-memory state fixture that simulates the resume scenario without disk I/O. Alternatively, run the second phase on the same state object directly. | File: tests/test_sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. RunState.create persists synchronously at construction (state.py create(): artifacts dir mkdir, working.html write, _write_status) -- there is no separate save() step; durable-on-write is the class's core contract (G4 'survives restarts'). RunState.load in the test therefore reads real on-disk state written moments earlier, deterministically. The 'test isolation / file-system side effects' objection inverts the test's purpose: disk-backed resume IS the feature under test (TICKET-0174); an in-memory fixture would test nothing. The test passes reliably. No change made.
