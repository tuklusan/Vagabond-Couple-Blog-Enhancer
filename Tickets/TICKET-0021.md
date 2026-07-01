# TICKET-0021: [state.py] Unhandled malformed JSON in artifacts
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: read_artifact calls json.loads without exception handling. If an artifact file is corrupted or manually edited, it will raise an unhandled JSONDecodeError, potentially crashing the caller. | Suggestion: Catch json.JSONDecodeError (or ValueError) and return None or re-raise a custom exception. | File: orchestrator/state.py | Severity: warning
Steps to Reproduce: 
Notes: 
