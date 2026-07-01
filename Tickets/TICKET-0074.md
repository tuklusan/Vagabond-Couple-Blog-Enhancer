# TICKET-0074: [schema_builder.py] Missing type validation for context values causing malformed
Status: Open
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: Several context values are used without checking their types: etr_minutes may be None or a string, producing a bad ETR suffix; waypoints and stops are assumed to be lists but if they are strings they will be split into characters in build_haspart; covers and other string-valued fields are used directly without sanitization or length enforcement. | Suggestion: Validate and coerce inputs before use: ensure etr_minutes is a non-negative integer or omit it; check that waypoints/stops are lists (or split if strings); ensure all text fields are strings and truncate description appropriately. | File: orchestrator/schema_builder.py | Severity: warning
Steps to Reproduce: 
Notes: 
