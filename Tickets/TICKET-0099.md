# TICKET-0099: [nodes.py] TypeError when context values are None
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: Multiple GenerativeNode prompt builder functions use context.get(key, default) with a default, but if the key exists in context with value None, .get() returns None instead of the default. Concatenating None with a string (e.g., 'Origin: ' + None) raises TypeError, crashing the pipeline. | Suggestion: Replace context.get(key, default) with (context.get(key) or default) for string fields, or explicitly guard against None after retrieval. Also ensure list fields (like 'sections') are not None before calling len(). | File: orchestrator/nodes.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: all node prompt concatenations use (context.get('X') or '') so an explicit None value can't cause TypeError (follow-on to 0069 which only handled MISSING keys). Verified: all writer prompts build with every context value None.
