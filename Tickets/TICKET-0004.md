# TICKET-0004: [__main__.py] Unhandled directory as input
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: When --input is a directory, src.exists() is True but src.read_text() raises IsADirectoryError causing a traceback and non-zero exit, but no user-friendly error. | Suggestion: Add a check: if not src.is_file(): print(_ascii('input is not a file: ' + str(src))); sys.exit(1) | File: orchestrator/__main__.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
