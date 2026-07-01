# TICKET-0089: [test_validators.py] Incomplete malformed schema test
Status: Open
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The negative test for malformed schema only asserts that valid_json is False, but does not verify that present remains True. If the validator erroneously reports the schema as absent when malformed, this test would not catch it. | Suggestion: Add an assertion: assert schema_result['present'] is True when the input contains a script tag with malformed JSON. | File: tests/test_validators.py | Severity: warning
Steps to Reproduce: 
Notes: 
