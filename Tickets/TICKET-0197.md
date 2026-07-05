# TICKET-0197: [image_audit.py] Unvalidated API response type crashes audit
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: The code only checks `raw_verdict is None` after calling `vision_client.inspect_image()`. If the API returns a non-dict value (e.g., a malformed response, a string), the subsequent `raw_verdict.get(...)` raises an unhandled AttributeError, crashing the entire audit and discarding all in-memory progress. This violates the per-image resilience guarantee stated in TICKET-0168. | Suggestion: Wrap the verdict construction (lines ~233-275) in a try-except or add an `isinstance(raw_verdict, dict)` guard. On failure, degrade the image to PLAUSIBLE status and continue the loop, logging the incident. | File: orchestrator/image_audit.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. `raw_verdict` cannot be a non-dict, non-None value -- `vision_client.inspect_image`/`_inspect_with_models` always return the output of `_parse_json_verdict`, which is a closed dict-or-None function: both its strict-parse and balanced-brace-scan paths explicitly gate on `isinstance(obj, dict)` before returning anything, and the brace-scan can only ever extract `{...}` regions in the first place (structurally incapable of yielding a list/string/number). Verified empirically: feeding `_parse_json_verdict` a JSON string, array, number, `null`, and non-JSON garbage all return `None`, never any other type. The existing `if raw_verdict is None:` check therefore already covers every non-dict case. No code change made.
