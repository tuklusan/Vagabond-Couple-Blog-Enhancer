# TICKET-0145: [review_loop.py] Unhandled exceptions from state operations in document certific
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: run_document_certification calls state.get_working_html() and state.read_artifact() without try/except. If these raise (e.g., due to I/O errors or corrupted state), the certification step crashes, potentially aborting the entire pipeline instead of gracefully marking as UNCERTIFIED. | Suggestion: Wrap calls to state methods in a try-except, return a certification result with pass2_deterministic indicating failure and pass1_reviewer=None, and log the error. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: wrapped state.get_working_html() and state.read_artifact() in run_document_certification with try/except, degrading to a not-certified result on an I/O error instead of propagating.
