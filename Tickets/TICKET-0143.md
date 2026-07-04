# TICKET-0143: [sequencer.py] iterating_generative_node may halt run on per-item exceptions
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: The handler iterates over items and calls run_generative_node without per-item try/except. If an item raises an exception, the entire node halts, contradicting the design that these optional nodes never halt. | Suggestion: Wrap the per-item call in try/except, log the error, and continue with other items. | File: orchestrator/sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: wrapped the per-item spec_factory/run_generative_node call in iterating_generative_node's loop in try/except, treating any exception as a skipped item (matching the existing non-certify skip path) instead of letting it propagate and halt the node.
