# TICKET-0048: Writer reliability on tight-constraint nodes: floor bump + DeepSeek escalation
Status: Open
Priority: high
Type: improvement
Created: 2026-06-30
Description: step2f escalated (max_rounds) because openrouter/free is an inconsistent instruction-follower on tight constraints and the 800 writer token floor was too low for deepseek-v4-pro to finish reasoning AND emit content (measured: needs ~1500). Fixes: (1) REASONING_TOKEN_FLOOR 800->1600; (2) writer_client.chat(prefer_deepseek) reorders DeepSeek-first; (3) review_loop escalates the writer to DeepSeek after WRITER_ESCALATE_AFTER=2 consecutive objective-check failures (mirrors reviewer universal fallback); (4) hardened step2f/step3 prompts (never I/me, single line) and lowered their temperature. Verified: deepseek writer at 1500-2500 budget returns valid <=150-char we-voice descriptions.
Steps to Reproduce: 
Notes: 
