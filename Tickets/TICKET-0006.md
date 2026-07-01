# TICKET-0006: [config.py] Unsafe int conversion for ORCH_MAX_NODE_ROUNDS
Status: closed
Priority: High
Type: Bug
Created: 2026-06-30
Description: int(os.environ.get('ORCH_MAX_NODE_ROUNDS', '6')) raises ValueError if the variable is non-integer, crashing the config import. | Suggestion: Use try/except, log warning, and fall back to default 6. | File: orchestrator/config.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
