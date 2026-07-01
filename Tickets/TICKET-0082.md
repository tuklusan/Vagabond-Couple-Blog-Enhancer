# TICKET-0082: [test_context.py] Insufficient content verification for extracted fields
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: Several assertions only check the presence or length of extracted fields (stops, landmarks, waypoints, sections, existing_facts) but do not verify the correctness of their contents. For example, 'stops_extracted' checks len >=5 but could pass if stops are empty strings or wrong values. This risks false positives and missed regressions. | Suggestion: Add explicit checks against known expected values for these fields from the fixture, or at least verify that each element meets a format (e.g., non-empty, valid structure). | File: tests/test_context.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit); suites green.
