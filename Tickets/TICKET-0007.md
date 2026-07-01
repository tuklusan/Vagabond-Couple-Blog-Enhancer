# TICKET-0007: [config.py] Glob result sorted lexicographically instead of by timestamp
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: In resolve_doc, sorted(DOCS_DIR.glob(pattern)) sorts by name, which may not match the intended 'most recent' timestamped theme XML. | Suggestion: Sort by file modification time using sorted(..., key=lambda p: p.stat().st_mtime) or ensure timestamp format is lexicographically sortable. | File: orchestrator/config.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
