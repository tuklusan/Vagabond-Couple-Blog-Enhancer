# TICKET-0106: Route box Themes field holds the waypoint list (fields swapped)
Status: closed
Priority: high
Type: bug
Created: 2026-07-01
Description: step7: Route field shows only endpoints; Themes field contains the waypoint chain. Should be Route=full chain (Oakhurst->Fresno->...->Grand Canyon), Themes=actual themes (Route 66, Punjabi dhaba, Mojave geology). Fix step7 prompt/field mapping.
Steps to Reproduce: 
Notes: step7 prompt: Route=full stop chain (geographic_stops, joined by ->), Themes=topics inferred from section titles (NOT the waypoint list). Verified prompt inputs.
