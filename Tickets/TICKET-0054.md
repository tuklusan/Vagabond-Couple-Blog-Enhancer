# TICKET-0054: DeepSeek-no-web reviewer certifies geographic hallucination (Scandinavia for a CA-AZ trip)
Status: Open
Priority: critical
Type: bug
Created: 2026-06-30
Description: usa13v8: step8 Route-at-a-Glance generated 'Oslo, Norway; Gothenburg, Sweden; Copenhagen, Denmark; Berlin, Germany' for an Oakhurst CA -> Grand Canyon AZ road trip, and the DeepSeek (no web) reviewer CERTIFIED it. This is the core anti-hallucination guarantee failing: only the web-grounded Claude reviewer reliably catches geographic/factual hallucination. Reinforces TICKET-0002 (fund Anthropic) as the critical path. Interim mitigations: constrain step8 writer to ONLY use the extracted route waypoints/stops (no free invention), and add a deterministic check that RAAG items intersect the known route entities.
Steps to Reproduce: 
Notes: Implemented deterministic grounding for step8 Route-at-a-Glance (the node that hallucinated): writer now gets the grounded route_items() list (real H2 sections) and is told to use ONLY those; deterministic check requires exactly one <li> per grounded stop + >=70% coverage. Verified: the v8 Scandinavian output (Oslo/Gothenburg/Copenhagen/Berlin) is now REJECTED (4!=6 items, 1/6 grounded). route_items() helper available for other route nodes. Remaining G2 gap is source-prose 'Landscape' (new ticket).
