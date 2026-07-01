# TICKET-0086: [test_node_loop.py] No exception handling around live API call
Status: Open
Priority: High
Type: Task
Created: 2026-07-01
Description: The call to review_loop.run_generative_node may raise exceptions (network errors, timeouts, malformed responses) that are not caught, causing the test to crash with a traceback instead of reporting a clean failure. This undermines test reliability in CI/CD pipelines. | Suggestion: Wrap the call in a try-except block that catches Exception, prints a standardized error message, and exits with code 1. | File: tests/test_node_loop.py | Severity: critical
Steps to Reproduce: 
Notes: 
