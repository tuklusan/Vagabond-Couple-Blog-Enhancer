# TICKET-0141: [review_loop.py] Unsafe integer parsing for environment variables
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: The module-level lines `WRITER_ESCALATE_AFTER = int(os.environ.get("ORCH_WRITER_ESCALATE_AFTER", "2"))` and `REVIEWER_ESCALATE_REROLLS = int(os.environ.get("ORCH_REVIEWER_REROLLS", "2"))` can raise a `ValueError` if the environment variable is set to a non-integer string. This unhandled exception during import will crash the application before any execution, posing a reliability and potential denial-of-service risk if an operator or attacker sets an invalid value. | Suggestion: Wrap each conversion in a try‑except that falls back to the default value, for example: `try: WRITER_ESCALATE_AFTER = int(os.environ.get("ORCH_WRITER_ESCALATE_AFTER", "2")) ; except ValueError: WRITER_ESCALATE_AFTER = 2`. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: wrapped review_loop.py's WRITER_ESCALATE_AFTER/REVIEWER_ESCALATE_REROLLS int(os.environ.get(...)) in try/except with the default fallback. Also fixed the identical latent pattern in reviewer_client.py (REVIEWER_DEEPSEEK_TOKEN_FLOOR), writer_client.py (REASONING_TOKEN_FLOOR), and sequencer.py (MAX_PASS1_BOUNCES) for consistency -- all 4 module-level int-env-var reads can no longer crash the import on a malformed override.
