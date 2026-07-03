# TICKET-0134: Original source's own ad-hoc 'continues at [link]' sentence now competes with the new lead-out feature
Status: Open
Priority: Medium
Type: Improvement
Created: 2026-07-03
Description: With the new lead-in/lead-out feature (0132) active, a source post that already had its own ad-hoc forward-reference sentence (e.g. arsenalna original: 'Our photo-story of wandering Kyiv continues at [Kyiv post link]') keeps that ORIGINAL sentence untouched (G3 byte-preservation) while the NEW step10 lead-out paragraph is appended after it, pointing to a DIFFERENT post (the real 'next' post, e.g. Georgia). Result: two consecutive 'continues at X' style sentences pointing to different posts, read as disjointed by G2 Pass-1 ('closing paragraphs tacked on after the concluding link, creating a disjointed ending'). The human POSTED workflow's output does NOT have this problem because the operator was authorized to rewrite the original author's language and simply dropped/replaced that ad-hoc sentence with the proper lead-out. IMPLEMENTATION NOTE for a future fix: this requires identifying the original's own now-redundant forward-reference sentence (when its target matches prior_post's URL, i.e. it's pointing to the SAME post as the new lead-in already covers) and removing/merging it -- a genuine content edit, not just a prompt tweak, and needs care to not silently break G3 href preservation for hrefs that are NOT the redundant one. Deferred -- lower priority than the fabrication-class bugs (0127/0129/0131/0133) already fixed this cycle.
Steps to Reproduce: 
Notes: 
