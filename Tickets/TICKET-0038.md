# TICKET-0038: [dev_review.py] Test file classification misses common 'test' directories
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The classify function marks a file as 'test' only if its name starts with 'test_' or if any path component equals 'tests' (case-insensitive). It does not match directories named 'test' (singular), which is a very common convention. This causes test files in such directories to be reviewed using the generic code-review prompt instead of the test-suite-specific prompt, reducing the relevance of the review. | Suggestion: Update the test-directory check to also match path components named 'test', for example by checking if 'test' or 'tests' appear in the lowercased parts list. | File: .claude/dev_review.py | Severity: warning
Steps to Reproduce: 
Notes: 
