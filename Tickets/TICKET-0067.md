# TICKET-0067: [context_extractor.py] Crash when DeepSeek returns None
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In derive_route_from_prose, if call_deepseek returns None (instead of a string), the subsequent check `if "{" in out` raises TypeError, crashing context extraction when LLM fallback is enabled. | Suggestion: Add a guard after the call: `if not isinstance(out, str): return {}`. | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: derive_route_from_prose guards 'if not isinstance(out, str): return {}' after call_deepseek. Verified import + logic.
