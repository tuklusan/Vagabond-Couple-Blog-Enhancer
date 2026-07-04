# TICKET-0166: [sequencer.py] Missing method `info` on Operator object risks crash in generativ
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-04
Description: In `generative_node` handler, code calls `sctx.operator.info(...)` when a node is skipped (optional) or escalated. But `StepContext.operator` is typed as `object` with no guaranteed `info` method. If the operator implementation lacks this method, it raises `AttributeError` and halts the sequence ungracefully. | Suggestion: Ensure the operator object always provides an `info` method, or wrap the call in a try/except and print/log the message as a fallback. | File: orchestrator/sequencer.py | Severity: critical
Steps to Reproduce: 
Notes: FALSE POSITIVE, NO ACTION. The `Operator` class (orchestrator/operator.py:27) defines `info()`, and every runtime construction site passes a real Operator instance: orchestrator/__main__.py:90 (`op = Operator(auto=args.auto)`), tests/test_sequencer.py, tests/test_full_sequence.py. The `operator: object` annotation on the StepContext dataclass is deliberately loose duck-typing (this single-module codebase has exactly one operator implementation), not a runtime gap -- there is no code path that constructs a StepContext with anything lacking `info`. Same theoretical-only-concern class as TICKET-0146/0147 (closed accepted-design). Adding try/except around every operator call would bury real operator-I/O failures; no code change made.
