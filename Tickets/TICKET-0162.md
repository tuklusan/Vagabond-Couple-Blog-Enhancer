# TICKET-0162: [assembler.py] Null input crash in assemble()
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: The function `assemble` does not validate that `html` is a string. If called with `None`, it calls `BeautifulSoup(None)` which raises `TypeError`, crashing the pipeline. | Suggestion: Add a guard at the start of `assemble`: `if html is None: raise ValueError('html must be a string')` or handle gracefully. | File: orchestrator/assembler.py | Severity: critical
Steps to Reproduce: 
Notes: Confirmed exploitable, not just theoretical: sequencer._assemble_working() (orchestrator/sequencer.py:484-491) sets src_html from state.read_artifact("pre_assembly_source"), falling back to sctx.state.get_working_html() when that artifact is missing/malformed -- either path can legitimately yield None before any working HTML has been set, which would previously crash deep inside BeautifulSoup with an opaque TypeError. Fixed by adding an explicit type guard at the top of assemble() that raises a clear ValueError instead. Full deterministic test suite (validators/context/assembler/document_cert/sequencer) re-run clean after the fix.
