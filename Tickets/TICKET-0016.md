# TICKET-0016: [reviewer_client.py] Multi-line API key file parsing error
Status: Open
Priority: Medium
Type: Bug
Created: 2026-06-30
Description: In load_anthropic_key(), if the key file has multiple lines and none start with 'ANTHROPIC_API_KEY=', the function returns the entire stripped file content as a single string, which will be invalid. This can happen if the file contains a newline or extra text after the key, e.g., a comment. | Suggestion: Only return the first non-empty line when no ANTHROPIC_API_KEY= line is found, or raise an error if the file contains multiple lines. For example: lines = [l for l in text.splitlines() if l.strip()]; if len(lines)==1: return lines[0].strip(); else: raise ValueError(...) | File: orchestrator/reviewer_client.py | Severity: warning
Steps to Reproduce: 
Notes: 
