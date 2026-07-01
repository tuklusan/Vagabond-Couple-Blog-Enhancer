# TICKET-0061: [assembler.py] YouTube embed XSS via unescaped user-provided title/caption
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: In `reemit_youtube`, the video title and caption extracted from the HTML are inserted directly into the template string via `str.replace` without any HTML escaping. If either value contains HTML special characters (e.g., `<script>alert(1)</script>`), the resulting HTML will be vulnerable to cross-site scripting (XSS). | Suggestion: Escape `vid`, `title`, and `caption` using `html.escape` (or the project's existing `_esc` helper) before performing the template substitutions. Alternatively, parse the template with BeautifulSoup and set the text content of the appropriate elements to avoid injection entirely. | File: orchestrator/assembler.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: reemit_youtube now escapes source-provided title (via _attr, double-quoted-attribute-safe incl. quotes) and caption (via _esc). vid is already regex-validated. Regression test added (no <script> injection from a malicious title/caption). Caught + blocked by the pre-push DeepSeek gate -- the gate working as designed.
