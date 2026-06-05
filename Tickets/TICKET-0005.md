# TICKET-0005: NVIDIA NIM 503 ResourceExhausted errors on Qwen3 Coder
Status: Fixed
Priority: Medium
Type: Bug
Created: 2026-06-05
Description: NVIDIA NIM returns 503 under load. No retry logic in code_agent.py. Requires manual retry.
Steps to Reproduce: 
Notes: Migrated primary coder from Qwen/NVIDIA NIM to DeepSeek API directly, eliminating NVIDIA NIM 503 errors for coding tasks.
