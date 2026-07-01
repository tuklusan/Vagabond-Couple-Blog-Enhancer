# TICKET-0023: [writer_client.py] Secrets file lines with spaces around '=' are missed
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: In _load_key, the check uses line.startswith(prefix + '='), but if the secrets file contains a line like 'OPENROUTER_AI_API_KEY = sk-...' (with spaces), it won't match and the fallback to raw text might return an incorrect key. | Suggestion: Either strip spaces around '=' when parsing, or use a proper .env parser. For example: key, val = line.split('=', 1); if key.strip() == prefix: return val.strip() | File: orchestrator/writer_client.py | Severity: warning
Steps to Reproduce: 
Notes: 
