# TICKET-0047: Writer returned chain-of-thought as answer (_extract_content reasoning fallback)
Status: closed
Priority: critical
Type: bug
Created: 2026-06-30
Description: On harder nodes (step3 summary block) openrouter/free (a reasoning model) emitted empty message.content and put its chain-of-thought in message.reasoning. _extract_content fell back to returning reasoning as the answer, so the node output was a 4000-char 'The user wants a summary block...' monologue -> repeated deterministic FAIL -> ESCALATE. Fix: _extract_content returns ONLY message.content; empty content now fails cleanly so _post_chat retries and chat() fails over to DeepSeek (which emits real content). Also hardened step3 narrator instruction (never I/me) and lowered its temperature to 0.2 for consistency.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
