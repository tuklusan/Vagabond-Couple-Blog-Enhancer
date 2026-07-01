# TICKET-0010: [nodes.py] Emoji detection regex overmatches non-emoji symbols
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: The _EMOJI_RE pattern includes many arrow and miscellaneous symbols (e.g., ←, ⇿, ⬀-⯿) that are not emoji. This causes valid titles containing symbols like arrows to be incorrectly rejected by the deterministic check. | Suggestion: Narrow the regex to match only actual emoji characters (e.g., U+1F300–U+1F5FF, U+1F600–U+1F64F, etc.) and avoid unrelated symbol blocks. | File: orchestrator/nodes.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
