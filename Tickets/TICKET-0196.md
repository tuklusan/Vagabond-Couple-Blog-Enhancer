# TICKET-0196: [nodes.py] Latent ImportError in title_deterministic_check
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: The function title_deterministic_check imports from .schema_builder at runtime. If the module or the variables _US_STATES/_CA_PROVINCES are unavailable, the check will raise an ImportError, bypassing the deterministic guard and potentially allowing fabricated titles to pass. | Suggestion: Move the import to the top of the file or handle the ImportError gracefully, e.g., with a fallback empty dict or logging an error and failing the check. | File: orchestrator/nodes.py | Severity: critical
Steps to Reproduce: 
Notes: VALID (low risk in practice -- schema_builder.py has no dependency back on nodes.py, so no circular-import motive existed for the local import), FIXED as suggested: moved `from .schema_builder import _US_STATES, _CA_PROVINCES` to the module-level imports, matching the existing `from . import validators` convention already at the top of the file. Verified `import orchestrator.nodes` succeeds standalone and the title-suffix tests still pass.
