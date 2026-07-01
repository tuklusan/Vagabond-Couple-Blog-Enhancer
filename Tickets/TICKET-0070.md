# TICKET-0070: [review_loop.py] Uncaught exceptions in prompt building methods
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: spec.build_writer_prompt() and spec.build_review_prompt() can raise exceptions (e.g., due to malformed spec or missing context) that are not caught, crashing the entire generation loop. Other error-prone steps (writer I/O, postprocessing) have explicit exception handling. | Suggestion: Wrap spec.build_writer_prompt(context, prior_output, revision) and spec.build_review_prompt(output, det_findings, context) in try-except blocks, returning an ESCALATE status with a descriptive reason on failure. | File: orchestrator/review_loop.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: build_writer_prompt and build_review_prompt wrapped in try/except in run_generative_node -> ESCALATE with reason build_writer/review_prompt_failed. Suites green.
