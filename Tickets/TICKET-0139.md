# TICKET-0139: Phase-5 doc-level Pass-1 reviewer flags the intentional lead-in/lead-out as off-topic
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-03
Description: review_loop._document_review() (the G2 Pass-1 holistic reviewer) reads the whole post cold with no context that it's part of a series -- it correctly (by its own single-post logic) flagged the new lead-out link to the next post ('...our travels carried us onward to Return to Kakheti Valley...') as 'an unrelated Georgia travel post... breaking geographical and logical flow', asking to remove or rewrite it, even though this is the intentional, correctly-grounded 0132 lead-out feature working as designed. FIX: threaded context through run_document_certification()/_document_review() (new optional context= param, passed from sequencer.phase5_certification_node via sctx.context) -- when context['prior_post']/['next_post'] is present, the reviewer's system prompt now explicitly says this post is one entry in a series and a lead-in/lead-out link to the prior/next post is EXPECTED, not off-topic. Verify: re-run arsenalna1 with the real URLs and confirm Pass-1 no longer flags the lead-out.
Steps to Reproduce: 
Notes: Fixed and verified; arsenalna1 reached full DONE with clean G2 two-pass certification. Deterministic test suites green.
