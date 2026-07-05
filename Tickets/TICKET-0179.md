# TICKET-0179: [image_audit.py] Uninitialized variables after exception cause NameError
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: In audit_images, the try block assigns local variables (img_bytes, mime, raw_verdict, raw_text, model). If an exception occurs during vision_client.fetch_image or .inspect_image, these variables are not assigned, but the code after the except block references them (e.g., if raw_verdict is None: and _transcript(state, model, ...)), raising a NameError that will crash the audit loop and potentially the entire program. | Suggestion: Initialize all variables to None before the try block, so that after catching an exception, the code can safely check for None and continue. | File: orchestrator/image_audit.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. The claimed NameError path is unreachable: every failure branch inside the per-image try block ends in `continue` or `break` (fetch-failure branch, exception branch, and the no-verdict branch all exit the loop iteration), so the post-try code that references raw_verdict/model executes ONLY when the try completed and assigned them. Empirical proof already in the suite: test_audit_survives_per_image_exception raises RuntimeError from inspect_image mid-audit and the loop continues cleanly (review_failures=1, next image audited, no NameError). No code change made.
