# TICKET-0211: [context_extractor.py] TypeError when schema description is not a string
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: In extract_context, (schema.get('description', '') or '')[:220] will raise TypeError if the description value is truthy but not a string (e.g., a dict), because Python does not support slicing on non-sequences. | Suggestion: Extract the description safely via _schema_name or force to string: description = str(schema.get('description', '')) if schema.get('description') else ''; ctx['covers'] = description[:220] | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED. schema.org permits object/array description values; `(schema.get('description','') or '')[:220]` slices whatever truthy value is present, so a dict description raises TypeError -- the exact class TICKET-0092 guarded on hasPart names/descs, missed at the top-level description. Fixed with an isinstance(desc, str) gate (non-strings yield covers=''). Test: test_non_string_schema_description_safe (a TravelAction whose description is an object extracts cleanly).
