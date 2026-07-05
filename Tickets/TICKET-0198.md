# TICKET-0198: [vision_client.py] No download size limit enforcement in fetch_image
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: fetch_image downloads the full response body via resp.content before checking its length against MAX_IMAGE_BYTES. An attacker can provide a URL to a very large file (e.g., 1GB) causing memory exhaustion and denial of service in the pipeline. | Suggestion: Set stream=True in the request and read up to MAX_IMAGE_BYTES+1 bytes incrementally, aborting the download and returning an error if the limit is exceeded before the entire file is transferred. | File: orchestrator/vision_client.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED exactly per the suggestion. `context_extractor.safe_get` gained an opt-in `stream` parameter (default False, so fetch_post_gist's behavior is unchanged); `vision_client.fetch_image` now requests with `stream=True` and reads the body via a new `_read_capped()` helper that consumes `resp.iter_content()` chunk-by-chunk, aborting (and closing the connection) the instant accumulated bytes exceed MAX_IMAGE_BYTES -- `.content` is never touched, so a multi-GB (or lying-Content-Length) response cannot be buffered into memory before the size check. Test: test_fetch_image_aborts_oversized_stream_without_buffering (a fake streaming response 50x the cap is rejected, its `.content` property is proven never accessed, and the connection is closed). Live regression-checked: real Blogger and Wikimedia image fetches still succeed byte-identical to before.
