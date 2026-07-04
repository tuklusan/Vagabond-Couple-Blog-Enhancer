# TICKET-0151: [README.md] Undocumented `--approve-phase4` flag
Status: closed
Priority: High
Type: Task
Created: 2026-07-03
Description: The Usage example shows the flag `--approve-phase4` but the flags table does not list or describe it, and the description of `--auto` does not mention this override. Users cannot know whether it is valid or what it does. | Suggestion: Add `--approve-phase4` to the flags table with a clear description (e.g., "Override the default Phase 4 approval withholding when used with `--auto`.") and update the `--auto` description to reference it. | File: README.md | Severity: critical
Steps to Reproduce: 
Notes: Fixed: added --approve-phase4 to the usage synopsis and flag table, explaining it's the test/CI opt-in to auto-grant Phase 4 approval under --auto.
