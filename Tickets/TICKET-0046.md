# TICKET-0046: Reviewer misreads ETR as travel time (should be Estimated Time to Read)
Status: Open
Priority: high
Type: bug
Created: 2026-06-30
Description: In the usa13full run the DeepSeek reviewer flagged 'ETR: 6 min.' as an unrealistic driving time and demanded 'approx 8-9 hours'. ETR = Estimated Time to READ (reading minutes, computed deterministically from word count), a locked value. Fix: define ETR in step2f writer+review prompts and instruct the reviewer not to flag/alter it. Verified: step2f now CERTIFIED.
Steps to Reproduce: 
Notes: 
