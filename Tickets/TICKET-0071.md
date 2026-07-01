# TICKET-0071: [review_loop.py] Possible NoneType error in document certification
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: run_document_certification() passes state.get_working_html() directly to document_deterministic_checklist() and _document_review(). If get_working_html() returns None (e.g., incomplete state), slicing or processing None will cause an unhandled exception, aborting certification. | Suggestion: Check if html is None or empty after retrieval, and return an early non-certified result or handle the error gracefully. | File: orchestrator/review_loop.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed: run_document_certification returns a non-certified result on None/empty working HTML instead of crashing. Verified.
