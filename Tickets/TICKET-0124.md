# TICKET-0124: Phase 5 doc-review max_tokens too low, truncated JSON forces unlocalizable ESCALATE
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: review_loop._document_review() called reviewer_client.certify() with max_tokens=2048. On the arsenalna1 run, DeepSeek's multi-criteria verdict (several repetition findings) got cut off mid-JSON, extract_verdict() failed to parse it, and certify() forced a synthetic ESCALATE with no criteria/revision_instructions. Since ESCALATE has no scoreable content, _drop_flagged_factoid() found nothing to bounce on and the whole Phase 5 cert halted for the operator even though the actual review was likely reachable with more headroom. Fix: bumped max_tokens 2048 -> 4096 in _document_review(). Verify by re-running arsenalna1.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
