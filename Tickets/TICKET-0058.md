# TICKET-0058: Document review truncates post to 18000 chars -> false 'truncated content' REVISE
Status: Open
Priority: high
Type: bug
Created: 2026-07-01
Description: usa13v10 reached Phase 5 with a clean deterministic Pass 2 (8/8) but halted because Pass 1 (DeepSeek holistic review) returned REVISE claiming the post 'ends abruptly with unclosed <p> ... region's'. Root cause: _document_review sent only html[:18000]; the assembled post is 28249 chars, and char 18000 falls mid-sentence at 'the region's'. The post is actually complete/well-formed. deepseek-v4-pro has 1M context. Fix: raise cap to 200000 (effectively full post). Verified: Pass 1 now CERTIFIED (html_sanity/repetition/smooth_read all pass).
Steps to Reproduce: 
Notes: 
