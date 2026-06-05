# TICKET-0007: step7_review.py reads only first 8000 chars
Status: Fixed
Priority: Low
Type: Enhancement
Created: 2026-06-05
Description: DeepSeek review limited to 8000 chars. Large posts may have issues missed.
Steps to Reproduce: 
Notes: step7_review.py rewritten: reads full HTML (no 8000 char limit), temperature=0.2, ASCII-safe prints.
