# TICKET-0120: [sequencer.py] Unhandled exceptions during state mark operations
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In run_sequence(), after calling each node's handler, the code calls sctx.state.mark_node() and sctx.state.log() without any try/except. If these durable-state operations raise an exception (e.g., due to I/O errors, storage failures, or malformed data), the exception propagates uncaught, aborting the whole sequence without a graceful halt and leaving the state inconsistent. This violates G4's requirement that the prior step must be confirmed complete in durable state before the next starts, and may cause data loss or corruption. | Suggestion: Wrap the mark_node and log calls in a try/except block. On failure, return a _halt result with an appropriate error message, so the sequence stops cleanly and the failure is recorded durablely if possible. | File: orchestrator/sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: run_sequence wraps the per-node mark_node/log durable writes in try/except -> clean _halt('durable-state write failed') instead of an uncaught abort. _halt itself now best-effort-persists (never masks the halt on a state-write failure). Verified import + full_sequence test.
