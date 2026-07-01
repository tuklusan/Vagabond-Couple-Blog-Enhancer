# TICKET-0040: [README.md] License prohibits execution but README provides usage instructions
Status: Closed
Priority: High
Type: Task
Created: 2026-06-30
Description: The license header states 'No execution, modification, redistribution, production use, or AI/ML training' but the README includes full installation and usage instructions (including CLI commands) as if readers are permitted to run the software. This is internally inconsistent and may lead to license violations. | Suggestion: Either remove the execution restriction from the license and allow usage, or add a prominent notice at the top of the README that the software is view-only and must not be executed, and remove the usage instructions (or move them to a separate, non-public document). | File: README.md | Severity: critical
Steps to Reproduce: 
Notes: Kept the license strict (view-only). Added README notes clarifying the Install/Usage sections are descriptive of how the software works, not a grant to execute/deploy; use is governed solely by LICENSE.
