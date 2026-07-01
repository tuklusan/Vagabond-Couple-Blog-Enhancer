# TICKET-0044: Writer empty-content on reasoning models: enforce max_tokens floor
Status: closed
Priority: high
Type: bug
Created: 2026-06-30
Description: Root cause of the 'provider exhaustion' blocker on TICKET-0001. Both configured writer models (openrouter/free, deepseek-v4-pro) are reasoning models that spend output tokens on internal reasoning before emitting the visible answer. Nodes with tight budgets (writer_max_tokens 200-400) and derive_route_from_prose (400) could have their whole budget consumed by reasoning, returning empty content -> spurious ESCALATE, misread last session as DeepSeek exhaustion. Fix: REASONING_TOKEN_FLOOR (default 800, env WRITER_TOKEN_FLOOR) applied in writer_client._post_chat. Verified: call_deepseek(max_tokens=20) returns content; derive_route_from_prose on USA-2024-part-13 returns full route.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
