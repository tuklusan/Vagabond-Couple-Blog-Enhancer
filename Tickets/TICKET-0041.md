# TICKET-0041: [README.md] Missing repository clone step before installation
Status: closed
Priority: Medium
Type: Task
Created: 2026-06-30
Description: The 'Install' section begins with 'pip install -r requirements.txt' without instructing users to clone the repository or navigate to the project directory. New users may not know where to find the file. | Suggestion: Add a step before 'pip install': 'git clone <repo-url> && cd Vagabond-Couple-Blog-Enhancer'. | File: README.md | Severity: warning
Steps to Reproduce: 
Notes: Fixed and verified (see commit).
