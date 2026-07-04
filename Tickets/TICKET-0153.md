# TICKET-0153: reemit_youtube silently dropped a real <a href> inside a video caption (G3 violation)
Status: closed
Priority: Critical
Type: Bug
Created: 2026-07-03
Description: reemit_youtube()'s caption extraction only ever pulled TEXT out of the tr-caption <p> or the legacy loose-content-after-<br/> fallback (0126) -- never preserved an embedded <a href> inside that caption. Observed on the alaska-cruise post: a legacy embed's caption was 'Watch: <a href="https://youtu.be/e_24URmIKwo">MS Statendam, Holland America Line</a>' -- reemit_youtube extracted only the link TEXT and discarded the href entirely, so the final assembled doc was missing an original href, failing G2 Pass-2's hrefs_preserved check (byte-for-byte href preservation, rule G3). FIX: added assembler._safe_caption_html() -- walks the caption's child nodes and preserves a genuine <a href="http(s)://...">...</a> link verbatim (both href and text escaped), while dropping any OTHER tag/attribute and rejecting any non-http(s) href scheme, so this cannot reopen the XSS surface TICKET-0061 closed. Both the tr-caption-<p> path and the legacy loose-content path now build the caption as safe HTML (for the visible caption) plus separately as plain text (for the title attribute, which can't contain a tag). Verify: re-run the alaska-cruise post, confirm hrefs_preserved passes and the youtu.be credit link survives in the output.
Steps to Reproduce: 
Notes: Fixed and verified via alaska1 re-runs; deterministic test suites green.
