# TICKET-0006: Add retry logic to code_agent.py for 503 errors
Status: Fixed
Priority: Medium
Type: Enhancement
Created: 2026-06-05
Description: code_agent.py should retry with exponential backoff when NVIDIA NIM returns 503.
Steps to Reproduce: 
Notes: code_agent.py regeneration includes exponential backoff retry (up to 2 retries) on 503 and timeout for DeepSeek primary coder.
