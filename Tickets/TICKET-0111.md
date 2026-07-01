# TICKET-0111: Summary narrative leaks the 'ROWS:' delimiter
Status: closed
Priority: medium
Type: bug
Created: 2026-07-01
Description: parse_summary_fragment left 'ROWS:' at the end of the rendered narrative paragraph (usa13v13 L14). Strip LABEL:/NARRATIVE:/ROWS: markers fully from the narrative.
Steps to Reproduce: 
Notes: parse_summary_fragment strips standalone/trailing LABEL:/NARRATIVE:/ROWS: markers from the narrative. Verified: no ROWS: leak on the v13 fragment.
