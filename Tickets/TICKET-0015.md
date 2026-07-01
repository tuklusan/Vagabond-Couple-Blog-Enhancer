# TICKET-0015: [review_loop.py] Unhandled exceptions in document_deterministic_checklist
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The document_deterministic_checklist function calls several validators (e.g., validate_ld_json, count_more_tags) directly and accesses dictionary keys like ['ok'] that might not exist if the validator fails. An exception would propagate unhandled from run_document_certification, potentially aborting the certification step. | Suggestion: Wrap each validator call in try-except, catch Exception, and mark the check as failed in the output dict, or escalate if appropriate. | File: orchestrator/review_loop.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
