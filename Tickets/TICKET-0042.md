# TICKET-0042: [README.md] Default required-documents path is Windows-specific and unlikely to 
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The default path 'H:\My Documents\BLOG_STUFF\...' is hardcoded to a Windows drive letter and specific folder structure, causing the pre-check to halt unless users override ORCH_DOCS_DIR. This is not portable. | Suggestion: Change the default to a relative path within the project (e.g., './required-docs/') or clearly mark the default as an example and require users to set ORCH_DOCS_DIR. | File: README.md | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit).
