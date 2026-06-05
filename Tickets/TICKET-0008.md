# TICKET-0008: step1_fetch.py has hardcoded post title and blog ID
Status: Fixed
Priority: High
Type: Enhancement
Created: 2026-06-05
Description: Post title and blog ID are hardcoded. Should be passed as CLI args from orchestrator.
Steps to Reproduce: 
Notes: step1_fetch.py rewritten with --title (required) and --blog-id (optional) argparse args. Orchestrator updated to pass --title.
