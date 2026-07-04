# TICKET-0147: [state.py] Status persistence is not concurrency-safe
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: mark_node and set_current_node read the full status JSON, modify it, and write it back without any locking. If multiple threads call these methods concurrently, one thread's changes can be overwritten by another's, leading to lost node completions and incorrect resumption state. | Suggestion: Guard all read-modify-write cycles on status.json with a threading.Lock shared across the RunState instance. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: DUPLICATE, NO ACTION
