# TICKET-0043: [README.md] Inconsistent NVIDIA key file naming and env var name
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The file is named 'nvidia-api-keys.txt' (plural), while other key files use singular ('-key.txt'). Also the example environment variable is 'NVIDIA_API_KEY_CODING', which may be a typo for 'NVIDIA_API_KEY' or an unexpected name that could confuse users. If the code actually expects 'NVIDIA_API_KEY_CODING', the naming should be clarified. | Suggestion: Rename file to 'nvidia-api-key.txt' for consistency and ensure the environment variable name matches what the code expects; if it is 'NVIDIA_API_KEY_CODING', explain its purpose. | File: Config/_SECRETS/README.md | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit).
