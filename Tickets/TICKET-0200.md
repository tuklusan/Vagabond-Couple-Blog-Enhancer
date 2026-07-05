# TICKET-0200: [vision_client.py] Unhandled exception in fetch_image breaks no-raise contract
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: fetch_image's docstring states it never raises, but the call to _read_capped is outside any try-except. If _read_capped encounters a network error (e.g., ChunkedEncodingError) during iteration, the exception propagates uncaught, potentially crashing the entire audit pipeline. | Suggestion: Wrap the _read_capped call (and the subsequent content check) in a try-except that catches requests.RequestException, sets last_reason, and continues to the next size token. | File: orchestrator/vision_client.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED. The TICKET-0198 streaming rewrite left `_read_capped(resp, MAX_IMAGE_BYTES)` outside the surrounding try/except -- a connection dropped mid-body (requests.exceptions.ChunkedEncodingError/ConnectionError, both RequestException subclasses) after a successful status/headers would propagate uncaught, violating fetch_image's own 'never raises' docstring contract. Wrapped the _read_capped call in a try/except requests.exceptions.RequestException, records the error as last_reason, and continues to the next size-token retry (matching every other failure path in this function). Test: test_fetch_image_survives_mid_stream_error (a fake stream that yields one chunk then raises ChunkedEncodingError -> fetch_image returns (None, reason), never raises).
