# TICKET-0064: [README.md] Nvidia key filename confusion
Status: closed
Priority: Medium
Type: Task
Created: 2026-07-01
Description: The current file is named nvidia-api-key.txt (singular), but the documentation also references a legacy filename nvidia-api-keys.txt (plural) that is 'still accepted'. This may cause users to create the wrong file or be unsure which to use. | Suggestion: State the canonical filename clearly and note that the legacy plural form is only retained for backward compatibility; new setups should use the singular nvidia-api-key.txt. | File: Config/_SECRETS/README.md | Severity: warning
Steps to Reproduce: 
Notes: Covered by 0043 change: _SECRETS/README states singular nvidia-api-key.txt as canonical, plural as legacy back-compat.
