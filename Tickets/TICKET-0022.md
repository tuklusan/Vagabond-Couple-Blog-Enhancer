# TICKET-0022: step3: rewritten prose uses I/me instead of we/us
Status: Fixed
Priority: Critical
Type: Bug
Created: 2026-06-06
Description: Llama rewrite introduced first-person singular pronouns (I, me, my) violating writing rules. Writing rules explicitly require we/us only. step3 prompt must enforce this. Also caught by step8 writer in first test run.
Steps to Reproduce: 
Notes: step3_rewrite.py system prompt now explicitly enforces: narrator we/us/our NEVER I/me/my, exact block count preservation with [N] prefix, no merging/splitting. Model instructed to self-scan and fix pronoun violations before returning.
