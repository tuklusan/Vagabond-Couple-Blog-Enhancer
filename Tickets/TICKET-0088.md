# TICKET-0088: [test_validators.py] Weak phrase detection assertion
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The assertion 'any("conclusion" in t for t in terms_found) or any("naturally" in t for t in terms_found)' only requires one of the two targeted phrases to be detected, potentially hiding a failure to detect the other. Since the test string explicitly contains both 'in conclusion' and 'naturally', the test should verify both are found. | Suggestion: Change assertion to check that a term containing 'in conclusion' and a term containing 'naturally' are both present in terms_found, or split into two separate checks. | File: tests/test_validators.py | Severity: warning
Steps to Reproduce: 
Notes: Test hardening applied (see commit): 0085 non-empty only for CERTIFIED; 0086 wrap live call; 0087 broaden outage skip; 0088 assert BOTH phrases; 0089 assert malformed schema present=True. Deterministic suite green; live tests compile.
