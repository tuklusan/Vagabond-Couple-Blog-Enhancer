# TICKET-0093: [context_extractor.py] Unhandled exception in derive_route_from_prose can crash
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: derive_route_from_prose imports writer_client inside the function and calls call_deepseek. If the import fails (e.g., missing module) or the API call raises an uncaught exception, the entire extract_context will crash because no try-except surrounds the call to derive_route_from_prose. This can break the pipeline when LLM extraction is enabled. | Suggestion: Wrap the call to derive_route_from_prose in extract_context with a try-except block, or move the import to the top level with conditional fallback. Log the error and proceed with an empty dict. | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: extract_context wraps derive_route_from_prose in try/except -> {} on any error.
