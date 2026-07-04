# TICKET-0155: schema instrument used a verb-phrase method ('Sailed and drove') as a Vehicle name
Status: closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: schema_builder._instrument()'s fallback (added in 0128) used context['method'] verbatim as the Vehicle name whenever no structured vehicle dict/string existed. On a genuinely mixed-mode journey (a cruise ship AND a rental car -- the alaska-cruise post), the extracted method was the verb phrase 'sailed and drove', producing 'instrument': {'name': 'Sailed and drove'} -- grammatically wrong as a Vehicle proper-noun name (a verb clause, not a noun), and a partial regression of the very rule TICKET-0103 established (instrument must never be a method verb). FIX: _instrument() now only uses context['method'] as the fallback Vehicle name when it's a short 1-2 word noun-like term (e.g. 'escalator') without an 'and' conjunction; a multi-clause/verb-phrase method falls back to the safe generic 'Overland vehicle' instead of mangling it into a fake proper noun. The human POSTED workflow used real research to name the actual vessel ('MS Statendam and rental car') -- the orchestrator has no ship-name-extraction capability, so falling back to a safe generic default here is the correct anti-hallucination-safe choice, not a fabrication. Verify: re-run the alaska-cruise post and confirm instrument.name is no longer a verb phrase.
Steps to Reproduce: 
Notes: Fixed and verified via alaska1 re-runs; deterministic test suites green.
