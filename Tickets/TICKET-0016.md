# TICKET-0016: Orchestrator step count banner was wrong (said /7 with 8 steps)
Status: Fixed
Priority: Low
Type: Bug
Created: 2026-06-05
Description: Orchestrator printed Step N/7 even after step 8 was added. Fixed in this session by deriving total from len(steps).
Steps to Reproduce: 
Notes: Fixed when orchestrator was updated to add step 8.
