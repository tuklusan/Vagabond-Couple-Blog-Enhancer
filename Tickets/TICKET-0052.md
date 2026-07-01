# TICKET-0052: Step 9-F factoids / Step 13 separators halt run instead of skipping (optional)
Status: closed
Priority: high
Type: bug
Created: 2026-06-30
Description: rev-18 (lines 731/735) makes Step 9-F factoids per-section and skippable when no verifiable non-duplicative fact exists; zero factoids ('NONE ADDED') is valid. The sequencer treated step9f/step13 as mandatory, so a reviewer ESCALATE halted the whole run (usa13v7). Fix: generative_node(optional=True) -> on escalation, skip (add nothing, record reason) rather than halt; marked step9f and step13 optional. Assembler already only splices CERTIFIED non-empty fragments.
Steps to Reproduce: 
Notes: Fixed, committed, and verified across the usa13 end-to-end runs this session.
