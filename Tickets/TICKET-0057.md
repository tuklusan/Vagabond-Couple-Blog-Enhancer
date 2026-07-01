# TICKET-0057: Step 12: remediate forbidden words in SOURCE prose (e.g. 'Landscape')
Status: Open
Priority: medium
Type: improvement
Created: 2026-07-01
Description: G2 no_forbidden scans the whole assembled doc incl. source prose. The USA-13 source contains 'Landscape' (1x), a forbidden descriptive word, so G2 fails even though all generated fragments are clean. rev-18 Step 12 reprases such violations in existing prose. Need: a Step 12 pass that detects scan_forbidden hits in source body prose and rewords them (generative + reviewer-certified, or a curated safe-synonym map for the specific marketing/cliche words), preserving meaning, links, and flow. Distinct from generated-content checks.
Steps to Reproduce: 
Notes: 
