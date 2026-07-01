# TICKET-0034: [test_validators.py] Missing negative and edge-case tests for validators
Status: Open
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The test only verifies validators against a single well-formed reference HTML. Functions like count_more_tags, validate_ld_json, scan_forbidden, and others are not tested with malformed input, missing elements, or error conditions, which could mask bugs in error handling or false negatives. | Suggestion: Add dedicated test cases for each validator that cover invalid HTML, missing tags, empty strings, JSON parse errors, and other boundary inputs. | File: tests/test_validators.py | Severity: warning
Steps to Reproduce: 
Notes: 
