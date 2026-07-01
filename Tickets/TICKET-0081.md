# TICKET-0081: [test_assembler.py] test_splice_order does not verify insertion position relativ
Status: Open
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The order check only ensures the relative order of fragment substrings (FIRSTPARA, ROUTEBOX, Route at a Glance) but does not verify they are inserted after the <!--more--> marker. If the fragments were accidentally placed before the marker (e.g., in the intro paragraph), the order test could still pass, giving a false sense of correctness. | Suggestion: Add an assertion that the fragments appear after the <!--more--> marker, e.g., check that their positions are greater than the position of '<!--more-->' in the output. | File: tests/test_assembler.py | Severity: warning
Steps to Reproduce: 
Notes: 
