# TICKET-0154: context sections included the post's own TITLE styled as a pre-fold H2, polluting summary/RAAG/hasPart
Status: closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: context_extractor.extract_context()'s sections list was built from ALL <h2> tags in the source with no positional filtering. On the alaska-cruise post (a legacy Blogger template), the post's own TITLE is itself styled as an <h2> sitting ABOVE the fold (before <!--more-->) -- a real content structure never touched by the rest of the pipeline (every genuine section H2 lives in the body, after the fold). Treating it as a 'section' produced a bogus first row everywhere sections are consumed: the Step-3 summary block ('...Full route overview' restating the whole post's scope instead of a real leg), and a garbled schema hasPart entry whose mined 'description' concatenated unrelated fragments including the literal route-box field labels 'Route:, Method:, Themes:'. FIX: context_extractor now walks the document in order and only collects <h2> text seen AFTER the <!--more--> comment (if present) -- an H2 above the fold is the post's own title/header material, not a content section. Verify: re-run the alaska-cruise post and confirm sections[0] is a real first content section, not the post title.
Steps to Reproduce: 
Notes: Fixed and verified via alaska1 re-runs; deterministic test suites green.
