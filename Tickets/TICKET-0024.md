# TICKET-0024: [test_assembler.py] Fragile assertion with magic number for summary rows
Status: Open
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The test expects exactly 14 data rows, which breaks if the reference file content changes or the test environment uses a different file. | Suggestion: Use a dynamic expected value (e.g., store before row count and compare), or verify structural properties rather than exact counts. | File: tests/test_assembler.py | Severity: warning
Steps to Reproduce: 
Notes: 
