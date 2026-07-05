# TICKET-0187: [vision_client.py] Base64 payload ceiling exceeded despite raw byte cap
Status: Closed
Priority: High
Type: Bug
Created: 2026-07-05
Description: MAX_IMAGE_BYTES is 160 KB but base64 encoding adds ~33% overhead, inflating the inline request to ~213 KB. The code declares a ~180 KB NIM inline-b64 ceiling, so requests may be rejected, breaking the visual audit. | Suggestion: Reduce MAX_IMAGE_BYTES to 130000 (130 KB) so that the base64-encoded size stays under 180 KB even with JSON overhead. | File: orchestrator/vision_client.py | Severity: critical
Steps to Reproduce: 
Notes: VALID, FIXED -- correct arithmetic: the ~180KB inline ceiling applies to the BASE64 payload (4/3 of raw), so the old 160,000-byte raw cap could admit a ~213KB encoded payload. Never observed live (s512-rj fetches ran 50-90KB), but latent. Fixed exactly per the suggestion: MAX_IMAGE_BYTES = 130_000, with the comment corrected to state raw-vs-encoded explicitly; images landing between the new and old caps fall to the existing s320-rj retry. No behavior change for any image seen so far.
