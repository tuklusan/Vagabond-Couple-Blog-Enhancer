# TICKET-0116: Prose enrichment gap: orchestrator preserves where workflow enriches
Status: closed
Priority: low
Type: improvement
Created: 2026-07-01
Description: Workflow deepens some original paragraphs with researched specifics (e.g. Ludlow ore-car stencil 'Ludlow Mining Company 1882 / Dynamite Car No.1'); orchestrator keeps the generic original. Consider an enrichment pass (fact-verified).
Steps to Reproduce: 
Notes: CLOSED won't-implement (by design / anti-hallucination): auto-enriching the AUTHOR'S ORIGINAL prose with new 'researched' facts requires web-grounded verification, which we do NOT have (reviewer is DeepSeek-only, no web). Injecting unverified facts into original prose would directly violate the #1 requirement (zero hallucination) and risks altering the author's voice/meaning. The Step 9-F section-closing factoids already ADD researched-caliber value at safe boundaries (6/6 in v16), fact-checked as far as the reviewer allows. Prose-body enrichment is deferred unless/until a web-grounded reviewer is funded (TICKET-0002, closed no-action).
