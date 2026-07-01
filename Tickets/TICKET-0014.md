# TICKET-0014: [review_loop.py] Unhandled exceptions from spec.postprocess and deterministic_ch
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: Both spec.postprocess and spec.deterministic_check are called without try/except. If either raises an exception (e.g., due to malformed writer output or a bug), the entire loop crashes, potentially losing progress and not escalating. | Suggestion: Wrap these calls in try-except blocks, log the error, and escalate with appropriate reason (e.g., 'postprocess_failed', 'deterministic_check_failed'). | File: orchestrator/review_loop.py | Severity: warning
Steps to Reproduce: 
Notes: 
