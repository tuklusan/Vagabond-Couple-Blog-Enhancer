# TICKET-0206: [sequencer.py] Image wrapping must happen BEFORE inventory/derivation, not at Phase-5 assembly
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: Follow-on to TICKET-0205, exposed by the very next peru1v1 resume: with wrap_bare_images running only inside Phase-5 assemble(), every earlier consumer of the working HTML still saw the unwrapped source -- the 1C inventory reported photos/tables mismatch (informational), the 1J audit's caption extraction would see no captions, and critically Step 13 derived its consecutive-image pairs from a document with 4 tables instead of 309, so the separators it generated did not cover the real adjacencies and Phase 5 G2 Pass-2 failed no_consecutive_images.
Steps to Reproduce: peru1v1 resume after TICKET-0205: image_table_match passes, no_consecutive_images fails.
Notes: Added `image_normalize_node()` ("Setup - Canonical image structure") to the canonical sequence immediately after lead-context and BEFORE all Phase-1 scans: it wraps bare photos in the WORKING HTML once, so 1C/1J/Step-13 all see the canonical structure. assemble() keeps its wrap call as an idempotent safety net (already-tabled images are untouched, so double-wrapping is impossible). Canonical sequence is now 29 nodes (README updated). For the in-flight peru1v1 run: step13_separator and phase5_generate were marked incomplete so the resume re-derives separator pairs from the wrapped document and reassembles; the new image_normalize node simply no-ops on the already-wrapped working HTML.
