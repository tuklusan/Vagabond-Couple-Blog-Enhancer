# TICKET-0098: [README.md] README contradicts license by encouraging execution
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: The README provides extensive installation, usage, and troubleshooting instructions while the proprietary license prohibits any execution, modification, redistribution, or production use. Although a note states the instructions are provided 'for reference — to explain how the software is structured and how it operates', the natural purpose of a README is to guide users in running the software, making it likely to be misinterpreted as permission. This inconsistency can mislead users into violating the license. | Suggestion: Either remove all operational instructions and clearly state that the project is not intended to be run, or change the license to allow execution (e.g., open-source or dual-licensing). If the instructions are meant only for the original author, move them to a separate internal document not included in the public README. | File: README.md | Severity: critical
Steps to Reproduce: 
Notes: ACCEPTED / duplicate of TICKET-0040 (operator decision): the README's Install/Usage sections are descriptive, not a grant -- the top blockquote already states they are 'for reference ... not a grant of permission to execute'. The strict view-only LICENSE governs. Recurring dev-review re-flag; design is intentional. No change.
