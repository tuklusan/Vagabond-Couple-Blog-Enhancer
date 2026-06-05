# TICKET-0004: code_agent.py goes to background when called from PowerShell
Status: Fixed
Priority: Medium
Type: Bug
Created: 2026-06-05
Description: PowerShell runs code_agent.py as background task. Workaround: store task in variable first.
Steps to Reproduce: 
Notes: Background tasks banned as canonical rule. code_agent.py now runs foreground. bypassPermissions set in settings.json.
