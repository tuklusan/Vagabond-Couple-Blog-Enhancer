# TICKET-0063: [README.md] Ambiguous bare-key behavior
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The README states that files may contain a bare key, but doesn't explain which environment variable that key corresponds to when placed in a given file. The examples all use NAME=value format, leaving it unclear whether a bare key in openrouter-api-key.txt sets OPENROUTER_AI_API_KEY or another variable. | Suggestion: Clarify that if a file contains just a key, the program maps it to the default environment variable for that provider (e.g., OPENROUTER_AI_API_KEY for openrouter-api-key.txt). Alternatively, recommend always using the NAME=value format and remove the mention of bare keys. | File: Config/_SECRETS/README.md | Severity: warning
Steps to Reproduce: 
Notes: _SECRETS/README: documented bare-key -> default env var mapping per file.
