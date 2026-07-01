# TICKET-0045: Reviewer DeepSeek verdict empty: enforce reviewer token floor
Status: closed
Priority: high
Type: bug
Created: 2026-06-30
Description: deepseek-v4-pro reviewer fallback must emit a full 5-criteria JSON verdict, but nodes cap review_max_tokens at 1000-1536. Reasoning consumes the whole budget, JSON never lands, empty content -> spurious ESCALATE on valid gate-passing output (observed on step2f_search_description in the usa13full run). Fix: REVIEWER_DEEPSEEK_TOKEN_FLOOR (default 3000, env REVIEWER_TOKEN_FLOOR) in reviewer_client._review_with_deepseek.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
