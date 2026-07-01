# TICKET-0083: [test_document_cert.py] Insufficient check on certification outcome keys existen
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The test checks that keys 'certified' and 'pass2_deterministic' are present, but does not verify their values (e.g., that 'certified' is True or matches pass2_deterministic). This could allow the test to pass even if certification failed. | Suggestion: Add assertions on the values, such as: check('certified_true', cert['certified'] is True) or check('certified_matches_pass2', cert['certified'] == cert['pass2_deterministic']). | File: tests/test_document_cert.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit); suites green.
