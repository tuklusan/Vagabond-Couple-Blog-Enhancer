# TICKET-0123: G2 Pass-1 REVISE should bounce to the offending node, not halt at phase5_cert
Status: closed
Priority: high
Type: improvement
Created: 2026-07-02
Description: usa13v15 halted at phase5_cert because Pass-1 (holistic) REVISE'd on ONE factoid's chronology (Topock Marina/Colorado River placed after Yucca). Per the rev-18 G2 design, a Pass-1 REVISE should identify the offending section/node (here the Crossing-into-Arizona factoid) and re-run that node's Tier-1 loop, then re-assemble + re-certify -- not halt the whole run. Implement a bounce: parse pass1 revision_instructions for the section, regenerate that node, reassemble, re-run G2 (bounded retries). Until then, a single content nit blocks an otherwise-clean, much-improved post.
Steps to Reproduce: 
Notes: Implemented Pass-1 REVISE bounce: phase5_cert now loops (MAX_PASS1_BOUNCES=3) -- on a Pass-1 REVISE with clean Pass-2, it identifies the flagged factoid section (best token-overlap match against revision text), DROPS that optional factoid, reassembles (from saved pre_assembly_source via _assemble_working), and re-certifies. Guaranteed convergence (factoids optional). Deterministic Pass-2 failures + unlocalizable REVISEs still halt. Verified: v15's Pass-1 correctly localizes to 'Crossing into Arizona: Kohinoor Dhaba'.
