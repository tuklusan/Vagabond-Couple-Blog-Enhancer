# TICKET-0165: [review_loop.py] Inverted more_canonical check certifies faulty documents
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: In `document_deterministic_checklist`, the `more_canonical` check passes when the count of extra canonical tags is non-zero (bad) and fails when it is zero (good), due to using `bool(fn())` where `fn()` returns an integer count. This can incorrectly certify documents with duplicate canonical tags or reject clean ones. | Suggestion: Change the lambda to explicitly return a boolean from the comparison: `lambda: validators.count_more_tags(html)['canonical_after_script'] == 0`. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. The reviewer's premise is wrong: `validators.count_more_tags(html)["canonical_after_script"]` is NOT an integer count -- it is defined as `after_script == 1` (orchestrator/validators.py:275), already a boolean that is True exactly when ONE <!--more--> sits immediately after the ld+json </script> (the canonical rev-18 placement). The integer count lives in the separate `after_script_count` key, which this check does not read. The existing lambda is therefore correct: it passes on canonical placement and fails otherwise -- verified by the long-standing test_document_cert.py `more_canonical` assertion against the known-good reference document. The reviewer's suggested fix (`... == 0`) would itself INVERT the check, failing every clean document and passing any document with zero canonical placements. No code change made.
