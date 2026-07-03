# TICKET-0121: [assembler.py] BeautifulSoup document used as replace_with target
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In reapply_summary_block(), new_node is a BeautifulSoup instance, not a Tag. Passing it to block.replace_with() may insert an entire HTML document tree (including <html> and <body> wrappers) instead of the intended div, corrupting the assembled page. | Suggestion: Replace 'block.replace_with(new_node)' with 'block.replace_with(new_node.div)' or 'block.replace_with(new_node.find("div"))' to extract the actual summary div. | File: orchestrator/assembler.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: added assembler._frag(html) returning the single top-level Tag (the case for every fragment we splice) so insert_before/after/replace_with never receive the BeautifulSoup document wrapper. Applied at all 8 insertion sites. Verified: G2 still clean, output structurally identical.
