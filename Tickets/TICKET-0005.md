# TICKET-0005: [__main__.py] Ignoring decode errors silently loses data
Status: closed
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: src.read_text(encoding='utf-8', errors='ignore') will silently drop bytes that are invalid UTF-8, potentially corrupting the HTML content without any warning, leading to parsing issues or missing content. | Suggestion: Consider using errors='replace' or errors='surrogateescape' to preserve information, or attempt to detect encoding (e.g., via chardet) before reading. | File: orchestrator/__main__.py | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Tests green.
