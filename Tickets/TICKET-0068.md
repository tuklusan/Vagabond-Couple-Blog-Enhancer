# TICKET-0068: [nodes.py] geographic_stops may produce 'None' stop name
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: In geographic_stops, when context.get('waypoints') or context.get('stops') contain None values, str(None) becomes 'None' and passes the strip check, resulting in a fake stop named 'None' in the route list. This can lead to hallucinated content. | Suggestion: Change list comprehension conditions to filter out None and falsy values: use 'if v and str(v).strip()' instead of relying solely on str(v).strip() to catch None. | File: orchestrator/nodes.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed: route_items + geographic_stops filter None/falsy (if v and str(v).strip()) so a None entry can't become a fake 'None' stop. Verified.
