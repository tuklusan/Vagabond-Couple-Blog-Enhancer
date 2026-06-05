# TICKET-0023: mistral-large-3-675b consistently times out on NVIDIA NIM
Status: Fixed
Priority: High
Type: Bug
Created: 2026-06-06
Description: mistral-large-3-675b-instruct-2512 on NIM times out every call (120s). May be 'coming soon' / not fully available in free tier. Used as: fallback coder and quality gate writer primary. Fallback already handles this via mistral-medium-3.5. Monitor for availability.
Steps to Reproduce: 
Notes: Replaced with nvidia/nemotron-3-super-120b-a12b which tests PASS on NIM. Confirmed working: temperature=1.0, top_p=0.95 per NVIDIA docs.
