# TICKET-0053: Step 9-F / Step 13 need per-section iteration (currently run once with empty subject)
Status: closed
Priority: medium
Type: improvement
Created: 2026-06-30
Description: Step 9-F (one factoid per H2 section) and Step 13 (one separator per consecutive-image pair) are inherently per-item, but run_generative_node is called once with the global context (no section_topic/subject), so the writer has no concrete subject and produces a clarifying question -> always skipped. Proper impl: sequencer iterates step9f over each H2 section and step13 over each consecutive-image pair from validators.consecutive_image_pairs, building per-item context (section_topic, subject, existing_facts) each time, and collects the certified fragments for assembly. Until then these steps add nothing (workflow-valid but minimal).
Steps to Reproduce: 
Notes: Implemented iterating_generative_node: Step 9-F iterates per H2 section (factoid each, placed at section end via assembler.insert_factoids), Step 13 iterates per consecutive-image pair (separator each). Per-item context now supplies section_topic/subject, fixing the empty-subject placeholder. Phase 5 consumes the lists. Step 12 findings-iteration deferred (prose modification risk) -- stays optional. Deterministic machinery tested; suites green.
