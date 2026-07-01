# TICKET-0009: [context_extractor.py] Crash on string-valued fromLocation/toLocation/instrument
Status: closed
Priority: High
Type: Bug
Created: 2026-06-30
Description: The code assumes these ld+json properties are dicts, but they can be plain strings per Schema.org. If they are strings, using .get('name') on them raises AttributeError, breaking the extraction. | Suggestion: Check type: if isinstance(loc, dict): use .get('name', ''); elif isinstance(loc, str): use the string directly. Apply similar for instrument. | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
