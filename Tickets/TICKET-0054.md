# TICKET-0054: DeepSeek-no-web reviewer certifies geographic hallucination (Scandinavia for a CA-AZ trip)
Status: Open
Priority: critical
Type: bug
Created: 2026-06-30
Description: usa13v8: step8 Route-at-a-Glance generated 'Oslo, Norway; Gothenburg, Sweden; Copenhagen, Denmark; Berlin, Germany' for an Oakhurst CA -> Grand Canyon AZ road trip, and the DeepSeek (no web) reviewer CERTIFIED it. This is the core anti-hallucination guarantee failing: only the web-grounded Claude reviewer reliably catches geographic/factual hallucination. Reinforces TICKET-0002 (fund Anthropic) as the critical path. Interim mitigations: constrain step8 writer to ONLY use the extracted route waypoints/stops (no free invention), and add a deterministic check that RAAG items intersect the known route entities.
Steps to Reproduce: 
Notes: Corrected RAAG grounding: per workflow line 356, Route at a Glance = one item per GEOGRAPHIC stop in travel order (NOT thematic H2 sections -- that is the summary block's job). Added geographic_stops() = origin+waypoints+destination; step8 now grounds in that (7 real stops for USA-13: Oakhurst->Grand Canyon) and its review prompt tells the DeepSeek reviewer to treat the grounded stops as authoritative (stops the reviewer was rejecting 'The Search for a Punjabi Dhaba' as non-geographic). Also fixed the G2 check: raag_h2_match (count==H2) was semantically wrong -> replaced with raag_nonempty. Tests green.
