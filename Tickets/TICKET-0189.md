# TICKET-0189: [vision_client.py] Unsafe string formatting in certification prompt
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: The _CERTIFY_PROMPT uses % formatting with user-supplied original and proposed text, which may contain '%' characters, causing TypeError and crashing the audit pipeline. | Suggestion: Replace with f-string or .format() to avoid interpreting '%' as format specifiers. | File: orchestrator/vision_client.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION -- the premise inverts how %-formatting works: '%' is only interpreted in the TEMPLATE, never in substituted VALUES. Verified empirically: _CERTIFY_PROMPT contains exactly the five intended %s specs and rendering with adversarial values ('Rain 100% of the time %s %(x)s {weird} 50%% off') succeeds with the value preserved verbatim. The suggested .format() replacement would INTRODUCE the very bug class claimed here (caption text containing literal '{}' braces would then raise KeyError/IndexError). Defense-in-depth already present regardless: image_audit wraps certify_correction in try/except and demotes any exception to a finding-only rejection, so even a real formatting error could not 'crash the audit pipeline'. No code change made.
