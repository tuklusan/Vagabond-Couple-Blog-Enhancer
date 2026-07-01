# TICKET-0092: [context_extractor.py] Potential crash when name in TravelAction schema is not a
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: The _schema_name function calls .strip() on the result of value.get("name", "") without ensuring it's a string. If the JSON contains a numeric name, this raises AttributeError, crashing the extraction. | Suggestion: Cast to string before stripping: str(value.get("name", "")).strip() | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: extract_context skips non-string schema part names and coerces non-string descriptions to None before concatenation -- no TypeError on Schema.org non-string values. Verified (name=123 skipped, real entry kept). Caught by the pre-push gate.
