# TICKET-0136: [nodes.py] Unsafe dict access on context values can crash writer
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: In step6_first_body_paragraph.writer and step10_journey_significance.writer, the code accesses prior_post["url"] and prior_post["title"] after checking if prior_post: but without verifying it's a dict. If context["prior_post"] is a string or other non-dict truthy value, this will raise TypeError or AttributeError, crashing the generation pipeline. Similarly in _with_lead_link_check, it calls post.get("url") without checking post is a dict. | Suggestion: Add a check like if isinstance(prior_post, dict) and prior_post.get("url"): before accessing keys, and similarly in the checker. | File: orchestrator/nodes.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: prior_post/next_post now normalized to None unless isinstance dict with truthy url, at both retrieval sites in step6/step10 and in _with_lead_link_check.
