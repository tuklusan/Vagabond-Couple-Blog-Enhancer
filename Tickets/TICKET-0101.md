# TICKET-0101: [test_assembler.py] Insufficient XSS validation in youtube caption test
Status: closed
Priority: High
Type: Task
Created: 2026-07-01
Description: The test 'no_raw_script_injected' only checks for the <script> tag, but the input snippet contains an onerror attribute that can execute JavaScript without a script tag. The test passes even if the output contains unescaped event handlers, potentially missing real injection vulnerabilities. | Suggestion: Expand the assertion to verify that attribute values are properly escaped, e.g., by checking that no unescaped HTML event handlers (such as 'onerror', 'onload') appear in the output, and that quotes within attributes are correctly encoded. | File: tests/test_assembler.py | Severity: critical
Steps to Reproduce: 
Notes: Strengthened test_youtube_caption_escaped: asserts no raw <script tag AND no title-attribute breakout (onerror=/unescaped quote). Core XSS fix (0061) verified.
