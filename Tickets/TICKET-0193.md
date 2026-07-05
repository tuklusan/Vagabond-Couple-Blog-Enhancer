# TICKET-0193: [image_audit.py] Unhandled exception in collect_image_records crashes audit
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: The function `collect_image_records` calls `BeautifulSoup(html, 'html.parser')` without a try/except. If the HTML is malformed, excessively large, or causes a parser error (e.g., MemoryError, recursion depth), the call will raise an exception that propagates uncaught, terminating the audit process entirely and losing all work. | Suggestion: Wrap `soup = BeautifulSoup(html, 'html.parser')` and the subsequent `find_all` in a try/except block. Log the error, return an empty records list, and report the failure to the caller so the audit can handle it gracefully without aborting. | File: orchestrator/image_audit.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED (same class as TICKET-0162's assemble() guard). Confirmed empirically: collect_image_records(None) and collect_image_records(12345) raised uncaught TypeError from BeautifulSoup ('Incoming markup is of an invalid type'); malformed-but-string HTML (unclosed tags, null bytes, deep nesting) was already handled fine by html.parser's tolerant parsing, so the real gap was type validation, not markup malformedness. Added an isinstance(html, str) guard returning [] for anything else. In the real pipeline this is unreachable (get_working_html() always returns str) -- defensive hardening for standalone/future callers, consistent with the project's established pattern. Test: test_collect_records_rejects_non_string_input (None/int/list/dict all -> []).
