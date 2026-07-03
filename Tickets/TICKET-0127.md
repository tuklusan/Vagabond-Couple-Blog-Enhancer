# TICKET-0127: step1_title writer fabricated a waypoint ('via Chernihiv') never mentioned in source, reviewer CERTIFIED it as fact
Status: closed
Priority: Critical
Type: Bug
Created: 2026-07-03
Description: On the arsenalna1 run (Kyiv metro-station post, no real waypoints/route -- origin==destination, single-location post), step1_title's prompt forces the 'Origin to Destination Overland via waypoints' format even when context.waypoints/landmarks are empty. The writer invented 'via Chernihiv' -- a real Ukrainian city, but never mentioned anywhere in the source HTML or extracted context -- and the DeepSeek reviewer CERTIFIED it, citing 'Wikipedia' as a source it never actually searched, with reasoning like 'Waypoint Chernihiv is a reasonable overland detour' (plausible != true). This is a genuine anti-hallucination failure landing in the highest-visibility field (the SEO title). FIX: (1) writer prompt now explicitly forbids inventing a waypoint and tells the writer to drop the 'Overland via' clause entirely for single-location posts (origin==destination, no waypoints); (2) added a deterministic guard in title_deterministic_check() that extracts any 'via X' clause and fails if X is not present in the known origin/destination/waypoints/landmarks/post_title context; (3) hardened the reviewer's FACTS criterion to explicitly fail on a real-but-absent-from-context place name, not just a nonexistent one. Verify: re-run arsenalna1, confirm no fabricated waypoint in the title.
Steps to Reproduce: 
Notes: Fixed and verified via arsenalna1 re-runs; deterministic test suites green.
