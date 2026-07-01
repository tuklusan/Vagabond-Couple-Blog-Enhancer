# TICKET-0002: Fund Anthropic API to enable web-grounded review
Status: closed
Priority: High
Type: Task
Created: 2026-06-30
Description: Anthropic key has zero credit balance; reviewer falls back to DeepSeek (no live web). Add credits so Claude web_search fact-checking activates.
Steps to Reproduce: 
Notes: CLOSED NO-ACTION (operator decision): Anthropic will not be funded on top of the $20 Claude plan. The reviewer is therefore permanently DeepSeek-only (no web). Consequence: the anti-hallucination guarantee must be enforced DETERMINISTICALLY (constrain writers to extracted/verified entities + deterministic route-intersection checks) rather than via web-grounded Claude review. See TICKET-0054.
