# TICKET-0095: [writer_client.py] _load_key crashes with NameError when secret file is missing
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In _load_key(), if the secret file does not exist, the variable 'text' is never assigned, yet the subsequent bare‑key fallback loop references 'text' unconditionally. This raises an unhandled NameError, crashing the writer when a key file is absent (instead of returning an empty string and failing gracefully with a 'key not found' error). | Suggestion: Initialize 'text' to an empty string ('') before the file‑existence check, or move the bare‑key fallback logic inside the 'if path.exists():' block so that it only runs when the file is present. | File: orchestrator/writer_client.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE (verified): both the NAME= loop and the bare-key loop are INSIDE 'if path.exists():' (line indentation); 'text' is always assigned when referenced, and the file-absent path falls through to 'return ""'. No NameError. Misread indentation. No change.
