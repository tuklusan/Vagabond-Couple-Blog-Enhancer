# TICKET-0021: step8: revised prose block count mismatch (29 vs 49)
Status: Fixed
Priority: High
Type: Bug
Created: 2026-06-06
Description: Writer returned 29 prose blocks but 49 were extracted. Reinsertion uses best-effort. Writer prompt must be stricter: return exactly N blocks, one per input block, preserving [N] prefix numbering.
Steps to Reproduce: 
Notes: Fixed three issues: (1) extract_prose now returns numbered [N] blocks not flat text. (2) writer prompt enforces exact block count and numbered return format (REVISED_PROSE: section). (3) reinsert_prose now parses [N] prefixes by index instead of splitting on double newlines.
