# TICKET-0147: [state.py] Status persistence is not concurrency-safe
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: mark_node and set_current_node read the full status JSON, modify it, and write it back without any locking. If multiple threads call these methods concurrently, one thread's changes can be overwritten by another's, leading to lost node completions and incorrect resumption state. | Suggestion: Guard all read-modify-write cycles on status.json with a threading.Lock shared across the RunState instance. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: Duplicate of TICKET-0146 (same status.json read-modify-write race, reworded). Already evaluated and closed accepted-design: the orchestrator has no code path with concurrent access to a run's state (strictly single-threaded, sequential node execution), and no locking dependency is currently used anywhere in the project to justify adding one for a race that cannot occur today. Deferred, not fixed -- see 0146's notes for full reasoning.
