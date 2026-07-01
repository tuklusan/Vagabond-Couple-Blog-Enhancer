# TICKET-0008: [config.py] Windows-specific default for DOCS_DIR
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: Default path uses Windows drive letter and backslashes, causing file detection failures on Linux/macOS if ORCH_DOCS_DIR is not set. | Suggestion: Use a relative path or document that ORCH_DOCS_DIR is mandatory on non-Windows platforms. | File: orchestrator/config.py | Severity: warning
Steps to Reproduce: 
Notes: 
