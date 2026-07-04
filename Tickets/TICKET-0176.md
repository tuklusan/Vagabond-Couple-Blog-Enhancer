# TICKET-0176: [nodes.py] SEO title stacks redundant state suffixes ("Ketchikan, AK, Glacier Bay, AK, and Denali National Park, AK")
Status: Open
Priority: Low
Type: Bug
Created: 2026-07-04
Description: alaska2v1's certified Step 1 title: "Vancouver, BC to Fairbanks, AK Overland via Ketchikan, AK, Glacier Bay, AK, and Denali National Park, AK" (104 chars). Three consecutive ", AK" suffixes read as keyword-stuffing, "Glacier Bay, AK" is awkward for a bay/park, and "Overland" is wrong for a route whose first half is a cruise (the hybrid cruise+drive assumption problem again -- same root cause family as TICKET-0155). A human title would state the state once: "... via Ketchikan, Glacier Bay, and Denali National Park, Alaska".
Steps to Reproduce: gen_step1_title artifact of run alaska2v1.
Notes: Candidate fixes: (a) title writer prompt: when multiple waypoints share a state/region, suffix only the last; avoid "Overland" when context['method'] indicates a mixed/cruise journey (context extraction already produces "sailed and drove"); (b) add a deterministic check flagging >=2 repeated ", XX" state suffixes so the reviewer loop must fix it. Low priority: title is usable and factually right, just stylistically weak vs the human gold standard.
