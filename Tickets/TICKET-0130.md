# TICKET-0130: Orphan text directly after <!--more--> (no wrapping <p>) reads as broken HTML once RAAG/route-box are spliced in
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-03
Description: Legacy Blogger sources sometimes put body text directly after <!--more--> with no wrapping <p> (e.g. arsenalna original: '<!--more-->Arsenalna station is named after...'). Harmless in the original, but once the orchestrator splices Route-at-a-Glance <ol> / route-summary box right before it, G2 Pass-1 correctly flagged it as broken HTML ('wrap the orphan text after the ordered list in a <p> tag'). The human POSTED workflow fixes this by wrapping it in a real <p>. FIX: added assembler.wrap_orphan_text() -- wraps top-level loose text found strictly AFTER the <!--more--> comment marker into a <p>. Deliberately scoped to top-level-only and after-more-only (not all <div> children, not pre-fold content) after an early broader version broke test_assembler's reference-fixture test (the fixture has a large top-level doc-comment preamble before <!--more--> that incidentally contains the phrase 'post summary', which got wrapped into a real <p> and confused validators.summary_block()'s regex search). Wired into assembler.assemble() right before reflow_blocks. Verify: re-run arsenalna1, confirm the section-opening prose after Route at a Glance is now inside a <p>.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
