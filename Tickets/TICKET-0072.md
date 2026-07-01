# TICKET-0072: [reviewer_client.py] Incorrect conversation continuation on pause_turn
Status: closed
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: When the model returns stop_reason='pause_turn', the code appends the assistant message to the conversation and continues without adding a user message. The Anthropic API requires alternating user/assistant roles; appending two assistant messages in a row is invalid. This can cause the conversation to fail or produce incomplete results, potentially forcing unnecessary fallback to DeepSeek. | Suggestion: On pause_turn, either send a user message with empty content to resume the conversation, or restart a new request with a fresh user message containing all previous context. | File: orchestrator/reviewer_client.py | Severity: warning
Steps to Reproduce: 
Notes: VERIFIED CORRECT (false positive): on stop_reason=='pause_turn' the append-assistant-content-and-re-request pattern IS Anthropic's documented pause_turn continuation (server-tool iteration), not a normal role-alternation violation. max_continuations caps the loop. No change.
