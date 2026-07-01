# TICKET-0059: Doc Pass-1 blocks delivery on out-of-scope factual asides despite all criteria passing
Status: closed
Priority: high
Type: bug
Created: 2026-07-01
Description: usa13v11: Pass-1 holistic review returned all three in-scope criteria (html_sanity, repetition, smooth_read) as PASS, but decision=REVISE because DeepSeek volunteered memory-based factual corrections to the SOURCE prose (CA-41 vs CA-99, Mojave Preserve) -- out of scope for Pass 1 and unverifiable (no web). This halted delivery. Fix: (1) prompt now says judge ONLY the 3 criteria, do NOT fact-check, set CERTIFIED iff all pass; (2) _pass1_ok certifies when all in-scope criteria pass regardless of a stray REVISE; asides remain recorded as advisory. Facts remain the remit of 1A/Step 12/per-node loops.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
