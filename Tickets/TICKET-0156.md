# TICKET-0156: step3_summary_block writer_max_tokens too small for a post with many H2 sections
Status: closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: step3_summary_block's writer_max_tokens=900 (review_max_tokens=1536) was tuned against posts with ~6-14 sections. On the alaska-cruise post (17 real sections after the 0154 fix), the writer needed a label + full narrative paragraph + one complete 'emoji | Section - descriptor' row per section in a SINGLE completion -- it kept truncating well short of 17 rows across every retry (2, 3, 6, 14 rows observed) and the node escalated to abort after max_rounds. call_deepseek() already floors max_tokens to REASONING_TOKEN_FLOOR=1600 for DeepSeek, but that floor -- tuned for tight/short nodes -- was still insufficient once DeepSeek's own internal reasoning is subtracted from the budget for a 17-row completion. FIX: bumped writer_max_tokens 900->2200 and review_max_tokens 1536->2400 for this node. Verify: re-run the alaska-cruise post and confirm step3_summary_block certifies with a full 17-row table.
Steps to Reproduce: 
Notes: Fixed and verified via alaska1 re-runs; deterministic test suites green.
