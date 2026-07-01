# TICKET-0017: [sequencer.py] Unsafe dict access in phase5_certification_node may raise KeyErro
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: In the handler for phase5_certification_node, if run_document_certification returns {'certified': False} without a 'pass2_deterministic' key (or if that key holds a dict without 'failed'), accessing cert['pass2_deterministic']['failed'] will raise a KeyError, causing an unhandled exception that halts the pipeline with a handler error instead of a graceful halt. This can obscure the real reason for certification failure. | Suggestion: Use safe access: failed = (cert.get('pass2_deterministic') or {}).get('failed', []). If that is still empty, fallback to the pass1_reviewer message as currently done, but ensure no KeyError is raised. | File: orchestrator/sequencer.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
