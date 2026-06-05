# TICKET-0020: step8: audit_notes UnboundLocalError when auditor fails
Status: Fixed
Priority: High
Type: Bug
Created: 2026-06-06
Description: When auditor_evaluate() fails (e.g. timeout), audit_notes is never assigned so the report writer crashes with UnboundLocalError. Fix: initialize audit_notes='' before the loop.
Steps to Reproduce: 
Notes: Fixed UnboundLocalError by unpacking auditor result into temp vars (_av, _an) then assigning to audit_notes, avoiding Python's local variable detection from tuple unpacking.
