# TICKET-0018: step8 writer system prompt conflates writer and editor roles
Status: Fixed
Priority: Medium
Type: Bug
Created: 2026-06-05
Description: step8_quality_gate.py writer prompt says 'professional writer and editor' which blurs role separation. Should say 'professional writer' only. Editor role belongs to auditor only.
Steps to Reproduce: 
Notes: Writer prompt in step8_quality_gate.py changed from 'professional writer and editor' to 'professional travel blog writer'. Editor role now belongs exclusively to auditor.
