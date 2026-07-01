# TICKET-0069: [nodes.py] Direct context key access may raise KeyError
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: Multiple GenerativeNode writer/review functions (e.g., step1_title, step6_first_body_paragraph, step7_route_summary_box) access context['origin'] and context['destination'] without checking existence, risking KeyError if these keys are missing from the context dictionary. | Suggestion: Replace direct access with context.get('origin', '') and similar defaults, or add explicit key checking and error handling to make the nodes robust to incomplete context. | File: orchestrator/nodes.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed: all node prompts use context.get('origin'/'destination','') -- no KeyError on incomplete context.
