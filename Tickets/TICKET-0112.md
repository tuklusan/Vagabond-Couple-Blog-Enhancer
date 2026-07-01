# TICKET-0112: Summary label uses ALL-CAPS route instead of series/part identity
Status: closed
Priority: medium
Type: improvement
Created: 2026-07-01
Description: label 'OAKHURST, CA -> GRAND CANYON, AZ - Post Summary'; POSTED 'Trans-America Part 13 - Post Summary'. Extract the post's series/part identity for the label; title-case; use em-dash not '->'.
Steps to Reproduce: 
Notes: context_extractor.extract_series derives 'Trans-America Part 13' from part-N in prev/next post links + 'Trans-America' in the intro; apply_prefold builds the summary label deterministically from series/post_title ('Trans-America Part 13 — Post Summary') instead of the writer's ALL-CAPS route. Verified on the fresh-run path.
