# TICKET-0050: Empty/garbage writer output passes deterministic check, triggers terminal ESCALATE
Status: closed
Priority: high
Type: bug
Created: 2026-06-30
Description: On step6 the free writer emitted 'User Safety: safe' (17 chars, a moderation artifact). standard_deterministic_check only checked forbidden words + narrator, so the junk passed to the reviewer, which correctly ESCALATED (no paragraph to certify) -- a terminal halt. Fix: add a substance guard -- global 40-char floor in standard_deterministic_check, plus prose_paragraph_check(120) for full-paragraph nodes (step6, step10). Too-short output now fails deterministically -> writer retry -> DeepSeek escalation, instead of terminal reviewer ESCALATE. Verified: junk rejected, real route paragraph passes.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
