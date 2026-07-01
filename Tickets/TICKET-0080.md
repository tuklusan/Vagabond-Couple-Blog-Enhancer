# TICKET-0080: [writer_client.py] Retry logic retries on all HTTP errors including client error
Status: Open
Priority: Medium
Type: Bug
Created: 2026-07-01
Description: In _post_chat, after handling 429/503 specially, it calls resp.raise_for_status() which raises HTTPError for other status codes (e.g., 400, 401). This exception is caught by the generic RequestException block and triggers a retry with backoff, leading to unnecessary retries for non-transient client errors. This wastes time and may cause the pipeline to appear hung on bad requests. | Suggestion: Rethink retry logic: only retry on 429, 503, network connectivity errors (e.g., timeout), and possibly empty content. For other HTTP errors, raise immediately. For example, after checking 429/503, if status_code is not in {429,503} and is an error, raise HTTPError without retry. Or catch HTTPError separately and do not retry. | File: orchestrator/writer_client.py | Severity: warning
Steps to Reproduce: 
Notes: 
