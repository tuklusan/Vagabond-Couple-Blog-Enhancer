# TICKET-0053: Step 9-F / Step 13 need per-section iteration (currently run once with empty subject)
Status: Open
Priority: medium
Type: improvement
Created: 2026-06-30
Description: Step 9-F (one factoid per H2 section) and Step 13 (one separator per consecutive-image pair) are inherently per-item, but run_generative_node is called once with the global context (no section_topic/subject), so the writer has no concrete subject and produces a clarifying question -> always skipped. Proper impl: sequencer iterates step9f over each H2 section and step13 over each consecutive-image pair from validators.consecutive_image_pairs, building per-item context (section_topic, subject, existing_facts) each time, and collects the certified fragments for assembly. Until then these steps add nothing (workflow-valid but minimal).
Steps to Reproduce: 
Notes: step12_resolve has the same per-item-with-empty-context problem as step9f/step13: it resolves violations flagged by 1H/1I, but those analysis passes are stubbed (no findings), so the writer emits a 'please provide the passage' placeholder that the reviewer rejects -> escalate/halt. Marked step12 optional so it skips cleanly when there is nothing to resolve. Proper impl (this ticket): implement 1H/1I to emit concrete findings and iterate step9f/step12/step13 per flagged item/section/image-pair.
