# TICKET-0118: Route at a Glance over-enumerates waypoints vs section-legs
Status: closed
Priority: low
Type: improvement
Created: 2026-07-01
Description: ORCH RAAG=7 pure geographic stops; POSTED=6 items mirroring the H2 sections (leg+descriptor). Refine 0054: align RAAG with section structure rather than every waypoint.
Steps to Reproduce: 
Notes: ACCEPTED design variance: POSTED RAAG uses 6 section-legs; orchestrator uses 7 geographic stops (geographic_stops). Both satisfy 'one item per stop in travel order' (workflow line 356); the geographic form was chosen because the DeepSeek reviewer rejects thematic section titles as non-geographic (0054). Descriptors are good. Not reverting.
