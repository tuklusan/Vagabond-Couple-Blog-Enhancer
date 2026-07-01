# TICKET-0026: [test_assembler.py] Test depends on mutable external file
Status: Open
Priority: Medium
Type: Task
Created: 2026-06-30
Description: test_reference_transforms relies on a file resolved at runtime; changes to the file or path could cause false failures. | Suggestion: Consider mocking the file contents or using a dedicated test fixture with known immutable content. | File: tests/test_assembler.py | Severity: warning
Steps to Reproduce: 
Notes: 
