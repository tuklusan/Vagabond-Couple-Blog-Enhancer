# TICKET-0135: Phase 5 doc-review max_tokens 4096 still occasionally too low for a verbose DeepSeek verdict
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-03
Description: TICKET-0124 bumped review_loop._document_review()'s max_tokens 2048->4096, which fixed the common case, but a particularly verbose DeepSeek repetition-findings list still got truncated on a later arsenalna1 run (raw_excerpt cut off mid- 'five-mi...' string), forcing another unparseable-verdict ESCALATE. FIX: bumped max_tokens 4096->6144, and added an explicit instruction to the reviewer system prompt to list at most the 3 most significant findings per criterion instead of enumerating every instance, reducing the chance of hitting any token ceiling. Verify: re-run arsenalna1 and confirm no more truncated-verdict ESCALATEs.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
