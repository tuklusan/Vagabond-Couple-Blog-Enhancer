# TICKET-0199: [context_extractor.py] Unvalidated waypoints type from LLM may corrupt context
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: In extract_context, when allow_llm is True and derive_route_from_prose returns a dict, the code uses derived['waypoints'] directly as a list without checking its type. If the LLM returns a string (valid JSON), slicing and joining will produce garbled text, corrupting ctx['waypoints'] and ctx['landmarks']. This could break downstream processors. | Suggestion: Before using, verify that derived['waypoints'] is a list (e.g., isinstance(derived.get('waypoints'), list)). If not, skip the assignment or convert appropriately. | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED. Confirmed empirically: derived['waypoints'][:5] on a bare string ('Foo, Bar, Baz'[:5] == 'Foo, ') and ', '.join(derived['waypoints'][:8]) on that same string produces character-level garbage ('F, o, o, ,,  , B, a, r') -- silent corruption, not a crash, exactly as described. The writer prompt instructs an array but a fallback/weak model can still emit a string. Fixed with an isinstance(derived_waypoints, list) guard before either the slice or the join; a non-list is treated as absent. Also defensively str()-coerces each element (in case an item itself isn't a string) before use downstream. Test: test_derived_waypoints_string_type_ignored (string form ignored + origin/destination still applied; well-formed list form still works).
