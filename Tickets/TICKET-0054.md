# TICKET-0054: DeepSeek-no-web reviewer certifies geographic hallucination (Scandinavia for a CA-AZ trip)
Status: closed
Priority: critical
Type: bug
Created: 2026-06-30
Description: usa13v8: step8 Route-at-a-Glance generated 'Oslo, Norway; Gothenburg, Sweden; Copenhagen, Denmark; Berlin, Germany' for an Oakhurst CA -> Grand Canyon AZ road trip, and the DeepSeek (no web) reviewer CERTIFIED it. This is the core anti-hallucination guarantee failing: only the web-grounded Claude reviewer reliably catches geographic/factual hallucination. Reinforces TICKET-0002 (fund Anthropic) as the critical path. Interim mitigations: constrain step8 writer to ONLY use the extracted route waypoints/stops (no free invention), and add a deterministic check that RAAG items intersect the known route entities.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
