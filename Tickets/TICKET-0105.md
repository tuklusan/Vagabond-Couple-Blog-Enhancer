# TICKET-0105: Route box fabricates distance/time (900km/2days vs actual 430mi/1day)
Status: closed
Priority: critical
Type: bug
Created: 2026-07-01
Description: step7 route box 'Distance/Time: Approx. 900 km / 2 days' is hallucinated (POSTED: 430 miles / 1 day). Do not fabricate distance/time; omit unless derivable, or mark clearly unknown.
Steps to Reproduce: 
Notes: step7 prompt: include Distance/Time ONLY if a real figure is provided; never invent (removed the [X]km/[Y]days template).
