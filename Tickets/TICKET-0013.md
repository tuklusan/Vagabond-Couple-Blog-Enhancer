# TICKET-0013: [review_loop.py] Unhandled exception from reviewer_client.certify breaks escalat
Status: closed
Priority: High
Type: Bug
Created: 2026-06-30
Description: In run_generative_node, the call to reviewer_client.certify is outside any try/except. If the reviewer service is down or a network error occurs, the exception propagates upward, crashing the node loop instead of escalating gracefully as designed. | Suggestion: Wrap reviewer_client.certify in try-except, catch Exception, log the error, and return an ESCALATE status with reason 'reviewer_unavailable'. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
