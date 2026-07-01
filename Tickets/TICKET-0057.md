# TICKET-0057: Step 12: remediate forbidden words in SOURCE prose (e.g. 'Landscape')
Status: closed
Priority: medium
Type: improvement
Created: 2026-07-01
Description: G2 no_forbidden scans the whole assembled doc incl. source prose. The USA-13 source contains 'Landscape' (1x), a forbidden descriptive word, so G2 fails even though all generated fragments are clean. rev-18 Step 12 reprases such violations in existing prose. Need: a Step 12 pass that detects scan_forbidden hits in source body prose and rewords them (generative + reviewer-certified, or a curated safe-synonym map for the specific marketing/cliche words), preserving meaning, links, and flow. Distinct from generated-content checks.
Steps to Reproduce: 
Notes: Implemented a conservative deterministic Step-12 pass: assembler.remediate_forbidden_prose swaps a CURATED set of forbidden descriptive/analytical/marketing words (never proper nouns -- landscape->scenery, realm->domain, etc.) in visible body text only, case-preserving. Wired into assemble(). Ambiguous words that can be place/section names (Foster, Explore, Pivot, Empower) are intentionally left for a future generative Step 12. Verified: on the usa13v8 body the full G2 deterministic checklist now passes 8/8 (schema_ok, more_canonical, image_table_match, no_consecutive_images, summary_present, no_ufffd, no_forbidden, raag_nonempty).
