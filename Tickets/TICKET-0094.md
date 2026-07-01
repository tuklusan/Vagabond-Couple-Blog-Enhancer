# TICKET-0094: [state.py] Path traversal in artifact saving due to unsanitized name
Status: closed
Priority: High
Type: Bug
Created: 2026-07-01
Description: The `save_artifact` method constructs the file path using `name + '.json'` without sanitizing `name`. If `name` contains path separators or '..', it could write files outside the run's artifacts directory, potentially overwriting important files. This can be exploited if artifact names are derived from untrusted input (e.g., user-provided content). | Suggestion: Sanitize `name` to only allow safe characters (e.g., alphanumeric + underscore/hyphen) or use `Path(name).name` to strip directory components. For example: `safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', name)` and then ensure it doesn't start with '.' or '-'? Alternatively, use `path = (self.artifacts_dir / name_only).resolve()` and verify it stays under artifacts_dir. | File: orchestrator/state.py | Severity: critical
Steps to Reproduce: 
Notes: Fixed: _safe_artifact_name sanitizes artifact names to a single safe component (save/read/has_artifact); path traversal blocked. Verified '../../evil/x'->'evil_x'.
