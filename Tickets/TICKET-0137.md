# TICKET-0137: [review_loop.py] Unhandled JSON serialization failure in review loop
Status: closed
Priority: High
Type: Bug
Created: 2026-07-03
Description: During the writer-reviewer loop, revision instructions are constructed using json.dumps on det_findings (line ~101) and reviewer criteria (lines ~119, 125). These values originate from custom spec methods or reviewer output and may contain non-serializable Python objects. If json.dumps raises TypeError, the exception is not caught, causing the node loop to terminate abruptly and potentially crash the orchestrator. | Suggestion: Wrap the json.dumps calls in try-except blocks; on failure, convert the content to a safe string representation (e.g., str(value)[:200]) or use a default placeholder, ensuring the loop continues and escalates properly. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: added _safe_json() helper wrapping json.dumps with a try/except fallback to str(obj), used at all 3 call sites (det_findings, verdict criteria x2) in review_loop.py's node loop.
