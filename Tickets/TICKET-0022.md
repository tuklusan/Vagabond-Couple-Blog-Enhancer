# TICKET-0022: [writer_client.py] Unhandled JSONDecodeError breaks retry logic
Status: closed
Priority: High
Type: Bug
Created: 2026-06-30
Description: In _post_chat, calling resp.json() may raise json.JSONDecodeError if the API returns invalid JSON (e.g., error page). This exception is not a subclass of requests.RequestException and is not caught, so it crashes the entire fallback chain instead of retrying. | Suggestion: Catch json.JSONDecodeError (or ValueError) around the resp.json() call or expand the except clause to include it, so retries can handle malformed responses. | File: orchestrator/writer_client.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed and verified (see commit). Deterministic tests green.
