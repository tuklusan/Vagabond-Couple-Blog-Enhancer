# TICKET-0051: Single stochastic reviewer ESCALATE terminally halts run; add re-roll + retry
Status: closed
Priority: high
Type: bug
Created: 2026-06-30
Description: The web-less DeepSeek reviewer fallback over-escalates verifiable facts (route/ETR it should know) and is inconsistent run-to-run: step2f certified in v2/v4/v5 but ESCALATED in v6 on identical-quality output, halting the whole run on round 1. Fix: on ESCALATE, re-roll the reviewer on the same content REVIEWER_ESCALATE_REROLLS=2 times; if still escalating, feed the concern back and continue (refine) rather than terminal-halt, escalating terminally only after MAX_NODE_ROUNDS. Fundamental fix for reliable web-grounded certification remains Anthropic funding (TICKET-0002).
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
