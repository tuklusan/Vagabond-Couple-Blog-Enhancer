# TICKET-0076: [state.py] `node_complete` incorrectly defaults missing `gates_ok` field to true
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: The method `node_complete` returns `bool(rec and rec.get('complete') and rec.get('gates_ok', True))`. When a status record exists but was written by an older version that omitted `gates_ok`, the default `True` would make the node appear complete even if its gates were not verified. This could allow a node to be treated as done when it should not be, potentially skipping necessary re-validation during resume. | Suggestion: Change the default to `False` so that a missing `gates_ok` field is treated as 'not OK' and the node is re-checked. For example: `rec.get('gates_ok', False)`. | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit); suites green.
