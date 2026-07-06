# TICKET-0210: [README.md] License-execution contradiction in README
Status: Closed
Priority: High
Type: Task
Created: 2026-07-05
Description: The LICENSE file states the software is view-only and prohibits execution, modification, or use. However, the README provides step-by-step instructions for installing dependencies, running smoke tests, and executing the orchestrator with various flags. These instructions guide users to perform actions that would violate the license. This creates a dangerous inconsistency that could lead to inadvertent license violations. | Suggestion: Align the documentation with the license: either remove execution-related instructions (install, usage, smoke tests, troubleshooting) and mark the software as view-only reference, or update the license to permit execution for evaluation purposes. | File: README.md | Severity: critical
Steps to Reproduce: 
Notes: DUPLICATE of TICKET-0190, closed ACCEPTED/NO ACTION the same day -- reworded ('License-execution contradiction in README' vs 0190's 'Executable instructions contradict view-only license') far enough that the title-token overlap (~0.11) fell under the 0183 fingerprint threshold, the same known matching limitation recorded on 0195. Verbatim resolution applies: the license's execution restriction binds LICENSEES; the Licensor documenting and running their own software in their own README is not bound by it, and no licensee obligation changes either way. Flagged to the repo owner once already as a business/legal framing question, not a code defect. No action.
