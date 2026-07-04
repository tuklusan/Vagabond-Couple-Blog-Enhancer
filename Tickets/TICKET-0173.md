# TICKET-0173: [sequencer.py] Single-word Step-12 needles can never localize (fixed >=2 overlap bar)
Status: Closed
Priority: Medium
Type: Bug
Created: 2026-07-04
Description: Observed live (alaska2v1): Step 12 resolved only 3/7 findings; all 4 skips were forbidden-word items ("Leverage", "Indeed", "Testament to", "Naturally") with reason "could not localize passage". Root cause: `_locate_flagged_passage` requires token-overlap score >= 2, but a single-word needle contributes at most 1 overlapping token -- so every one-word 1I finding was structurally unlocalizable, silently making the forbidden-word half of Step 12 a no-op.
Steps to Reproduce: Step 12 item with needle "Leverage" against a body containing the word; localization returned None before the fix.
Notes: Fixed: the bar now scales with the needle -- `best_score >= min(2, len(needle_toks))`. Multi-word needles keep the anti-false-positive >=2 requirement; single-token needles localize on their one exact token match. Test: test_locate_single_word_needle.
