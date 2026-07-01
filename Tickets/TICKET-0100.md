# TICKET-0100: [README.md] Contradictory execution instructions with view-only license
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: The README provides step-by-step commands to clone, install, and run the orchestrator (e.g., 'git clone', 'pip install', 'python -m orchestrator --input'), but the proprietary license strictly forbids execution. This inconsistency may mislead users into unknowingly violating the license terms. | Suggestion: Either amend the license to permit execution, or remove all execution-related instructions (install, usage, API key setup for running) and add conspicuous warnings that the software must not be executed under the current license. | File: README.md | Severity: critical
Steps to Reproduce: 
Notes: ACCEPTED / duplicate of 0040+0098 (operator decision, third re-flag): README Install/Usage are descriptive not a grant; top blockquote states so; strict view-only LICENSE governs. No change.
