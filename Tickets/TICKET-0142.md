# TICKET-0142: [sequencer.py] lead_context_node may halt run contrary to docstring
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: The handler accesses post['title'] without a .get(), so if fetch_post_gist returns a dict missing the 'title' key, a KeyError will halt the run. The docstring promises it 'never halts the run'. | Suggestion: Change to post.get('title', '') to avoid KeyError. | File: orchestrator/sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: post['title'] -> post.get('title', '') in lead_context_node.
