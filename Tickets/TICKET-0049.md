# TICKET-0049: Narrator check false-positives on interstate highways (I-40) and ME abbrev
Status: Open
Priority: high
Type: bug
Created: 2026-06-30
Description: writing_rules_findings flagged the 'I' in interstate designations (I-40, I-5, I-10) as the first-person pronoun because \bI\b treats the hyphen as a word boundary. On the USA-2024-part-13 post (an I-40 road trip) this made step3_summary_block escalate for 4 straight rounds on otherwise-valid DeepSeek output. Also the me check used IGNORECASE, which would flag 'ME' (Maine). Fix: exclude 'I' followed by optional hyphen+digit; make me case-sensitive. Verified against I-40/I-5/I-10/I-15/ME plus genuine first-person I/me.
Steps to Reproduce: 
Notes: 
