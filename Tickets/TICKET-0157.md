# TICKET-0157: Canadian province abbreviations not expanded/country-suffixed like US states (Vancouver, BC vs Fairbanks, Alaska, USA)
Status: closed
Priority: Low
Type: Improvement
Created: 2026-07-04
Description: schema_builder._full_place_name() only recognized 2-letter US state codes for expansion + country suffix -- a Canadian province abbreviation like 'BC' was left bare ('Vancouver, BC'), asymmetric with a US destination on the same trip getting the full treatment ('Fairbanks, Alaska, USA'). Not wrong, just inconsistent formatting. FIX: added _CA_PROVINCES (all 13 provinces/territories), mirroring _US_STATES -- a recognized province now expands + gets ', Canada' appended the same way a US state gets ', USA'. Observed on the alaska-cruise post (Vancouver to Fairbanks cruise+road-trip).
Steps to Reproduce: 
Notes: Fixed and verified via alaska1 re-runs; deterministic test suites green.
