# TICKET-0113: Source-prose typos not corrected (Kohnioor, contine)
Status: closed
Priority: medium
Type: improvement
Created: 2026-07-01
Description: Workflow fixes source typos ('Kohnioor'->Kohinoor, 'contine'->continue); orchestrator preserves them. Add a spelling/typo-correction pass on source prose (deterministic dictionary or reviewed).
Steps to Reproduce: 
Notes: DEFERRED to generative Step-12: a naive deterministic spell-checker is unsafe here (blog is full of non-English food/place words -- dhaba, pakoda, naan, Kohinoor, Yucca -- that would false-flag). Typo correction (Kohnioor->Kohinoor, contine->continue) needs the reviewed generative Step-12 pass, not a dictionary. Tracked under Step-12 work.
