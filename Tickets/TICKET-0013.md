# TICKET-0013: step3_rewrite.py API key loading may still have NVIDIA_API_KEY_CODING bug
Status: Fixed
Priority: High
Type: Bug
Created: 2026-06-05
Description: Earlier versions of step3_rewrite.py had a bug where NVIDIA_API_KEY_CODING was matched instead of NVIDIA_API_KEY when loading the key. The version in Scripts/ may or may not have been fixed. Needs verification.
Steps to Reproduce: 
Notes: Verified: step3_rewrite.py correctly uses startswith('NVIDIA_API_KEY=') and not startswith('NVIDIA_API_KEY_CODING=') — no bug present.
