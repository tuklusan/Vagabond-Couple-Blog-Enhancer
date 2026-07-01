# TICKET-0060: Assembler appends journey-significance + last-section factoid AFTER the sign-off outro
Status: closed
Priority: high
Type: bug
Created: 2026-07-01
Description: usa13final: Phase-5 Pass-1 correctly FAILED smooth_read -- the journey-significance paragraph (and the final section's factoid) are appended at the very end of the body, AFTER the post's sign-off ('Until next time, fellow wanderers - The Vagabond Couple and Shehzadi'), breaking the read. Per rev-18 body structure the Journey significance paragraph precedes the Next Stop outro. Fix: assembler inserts trailing generated content BEFORE the outro anchor (a 'Next Stop' H2 if present, else the sign-off paragraph), not append-to-end. Applies to splice_fragments journey_significance and insert_factoids for the last section. (Deterministic Pass-2 was clean; the reviewer gate caught this -- validates _pass1_ok.)
Steps to Reproduce: 
Notes: Fixed: assembler _outro_anchor + _append_before_outro insert journey-significance and last-section factoids BEFORE the sign-off/Next-Stop outro (not append-to-end). Regression test added. Verified: both land before 'Until next time' sign-off; no-outro case appends safely. Caught by the G2 Pass-1 reviewer -- validates the review gate.
