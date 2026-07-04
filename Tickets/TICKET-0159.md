# TICKET-0159: [context_extractor.py] SSRF vulnerability in fetch_post_gist
Status: closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: The function fetch_post_gist fetches any provided URL without validating the network location. Attackers could inject URLs pointing to internal services (e.g., cloud metadata, localhost APIs) leading to sensitive data exposure or further attacks. | Suggestion: Validate the URL to only allow known safe domains (e.g., the blog's own domain) or restrict to public IP ranges. | File: orchestrator/context_extractor.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: added _is_safe_public_url() -- rejects any URL that isn't a plain http(s) scheme or whose hostname resolves to a private/loopback/link-local/reserved/multicast IP (covers localhost, RFC1918 private ranges, and the cloud metadata endpoint 169.254.169.254). fetch_post_gist() now checks this before making any request; fails closed on any parse/DNS error. Verified: real public URLs still fetch, localhost/private-IP/file-scheme/malformed URLs are all correctly rejected.
