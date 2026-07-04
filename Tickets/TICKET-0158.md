# TICKET-0158: Consolidate 4 independent H2-scanning implementations into validators.body_h2_tags()
Status: closed
Priority: Medium
Type: Improvement
Created: 2026-07-04
Description: TICKET-0154 fixed the 'title-styled-as-pre-fold-H2' bug in context_extractor.py's sections list, but the same root pattern (blindly scanning ALL <h2> tags with no before/after-<!--more--> distinction) had been independently copy-pasted into 3 more call sites: sequencer._section_items() (Step 9-F factoid generation -- wasted a full writer/reviewer round-trip generating then bouncing a factoid for the bogus title-section on the alaska-cruise post), schema_builder._post_h2_sections() (hasPart entities), and schema_builder.build_haspart()'s h2_terms map. Consolidated all 4 into one new validators.body_h2_tags(html) -- the single source of truth for 'real content section H2s' -- and updated context_extractor.py, schema_builder.py (both sites), sequencer.py, and validators.raag_vs_h2() itself to call it instead of re-implementing the walk. Verified: full deterministic test suite green, re-ran the alaska-cruise post end-to-end with no Step-9F factoid generated for the bogus title-section.
Steps to Reproduce: 
Notes: Fixed in the same pass; deterministic test suites green.
