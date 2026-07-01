# TICKET-0097: [test_node_loop.py] Unhandled NoneType on output when outcome has output set to
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: outcome.get('output', '') returns None if the 'output' key exists with value None, causing AttributeError on .strip() in the output_nonempty check. This can lead to an ungraceful test crash. | Suggestion: Use output = outcome.get('output') or '' or handle None explicitly. | File: tests/test_node_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: test_node_loop uses outcome.get('output') or '' -> None-safe .strip().
